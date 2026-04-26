from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

import asyncpg

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # /app
QUIZ_SQL_PATH = PROJECT_ROOT / "resources" / "quiz import data.sql"
print(f"seeding variable: PROJECT_ROOT = {PROJECT_ROOT}")
print(f"seeding variable: QUIZ_SQL_PATH = {QUIZ_SQL_PATH}")

# Fixed lock ID, used by pg_advisory_lock to avoid concurrent seeding
SEEDING_LOCK_ID = 2026041201


class SeedingError(RuntimeError):
    pass


def _parse_database_url(url: str) -> dict[str, object]:
    """
    Parse DATABASE_URL like:
    postgres://user:pass@db:5432/askvigil_db
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise SeedingError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")

    db_name = parsed.path.lstrip("/")
    if not db_name:
        raise SeedingError("DATABASE_URL has no database name")

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": db_name,
    }


def _quote_ident(name: str) -> str:
    # Safe identifier quoting for CREATE DATABASE
    return '"' + name.replace('"', '""') + '"'


async def _connect(
    params: dict[str, object], database: str | None = None
) -> asyncpg.Connection:
    return await asyncpg.connect(
        host=params["host"],
        port=params["port"],
        user=params["user"],
        password=params["password"],
        database=database or params["database"],
    )


"""
Execute the external script:
It will execute external commands, such as:
    aerich upgrade
    seed_scam_categories.py
    import_open_data.py
    generate_embeddings.py
"""


async def _run_subprocess(cmd: list[str], cwd: Path) -> None:
    print(f"[Seeding] Running command: {' '.join(cmd)}")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if stdout:
        print(stdout.decode(errors="ignore"))
    if stderr:
        print(stderr.decode(errors="ignore"))

    if proc.returncode != 0:
        raise SeedingError(f"Command failed ({proc.returncode}): {' '.join(cmd)}")


"""
It will check whether the DATABASE exists. If not, CREATE DATABASE askvigil_db
"""


async def _ensure_database_exists(params: dict[str, object]) -> None:
    target_db = str(params["database"])
    admin_db = os.getenv("POSTGRES_ADMIN_DB", "postgres")

    conn = await _connect(params, database=admin_db)
    try:
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            target_db,
        )
        if exists:
            print(f"[Seeding] Database exists: {target_db}")
            return

        await conn.execute(f"CREATE DATABASE {_quote_ident(target_db)}")
        print(f"[Seeding] Database created: {target_db}")
    finally:
        await conn.close()


async def _table_exists(conn: asyncpg.Connection, table_name: str) -> bool:
    return bool(
        await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = $1
            )
            """,
            table_name,
        )
    )


async def _table_count(conn: asyncpg.Connection, table_name: str) -> int:
    # table_name comes from constants in code, not user input
    row = await conn.fetchval(f"SELECT COUNT(*) FROM {_quote_ident(table_name)}")
    return int(row or 0)


async def _has_any_business_tables(conn: asyncpg.Connection) -> bool:
    # Check for a specific table that defines a successful migration
    # 'scam_categories' is a good candidate since it's the first one you seed
    return await _table_exists(conn, "scam_categories")
    # return bool(
    #     await conn.fetchval(
    #         """
    #         SELECT EXISTS (
    #             SELECT 1
    #             FROM information_schema.tables
    #             WHERE table_schema = 'public'
    #               AND table_name NOT IN ('aerich')
    #         )
    #         """
    #     )
    # )


async def _run_aerich_upgrade() -> None:
    await _run_subprocess(
        [sys.executable, "-m", "aerich", "upgrade"],
        cwd=PROJECT_ROOT,
    )


async def _run_seed_scam_categories() -> None:
    await _run_subprocess(
        [sys.executable, "-m", "scripts.seed_scam_categories"],
        # [sys.executable, str(PROJECT_ROOT / "app/scripts/seed_scam_categories.py")],
        cwd=PROJECT_ROOT,
    )


async def _run_import_open_data() -> None:
    # Use -m and the dot-notation path relative to /app/app
    await _run_subprocess(
        [sys.executable, "-m", "scripts.import_open_data"],
        cwd=PROJECT_ROOT / "app", # Run from the directory where 'scripts' is a package
    )
    # await _run_subprocess(
    #     [sys.executable, str(PROJECT_ROOT / "app/scripts/import_open_data.py")],
    #     cwd=PROJECT_ROOT,
    # )


# phishing dataset batch import into database
async def _run_import_phishing_urls() -> None:
    await _run_subprocess(
        [sys.executable, "-m", "scripts.import_phishing_urls"],
        cwd=PROJECT_ROOT / "app",
    )
    # await _run_subprocess(
    #     [sys.executable, str(PROJECT_ROOT / "app/scripts/import_phishing_urls.py")],
    #     cwd=PROJECT_ROOT,
    # )


# async def _run_generate_embeddings() -> None:
#     await _run_subprocess(
#         [sys.executable, str(PROJECT_ROOT / "app/scripts/generate_embeddings.py")],
#         cwd=PROJECT_ROOT,
#     )


async def _run_quiz_sql(conn: asyncpg.Connection) -> None:
    if not QUIZ_SQL_PATH.exists():
        raise SeedingError(f"Quiz SQL file not found: {QUIZ_SQL_PATH}")

    sql = QUIZ_SQL_PATH.read_text(encoding="utf-8")
    print(f"[Seeding] Executing SQL file: {QUIZ_SQL_PATH}")
    await conn.execute(sql)
    print("[Seeding] Quiz SQL import completed.")


async def run_seeding() -> None:
    """
    End-to-end idempotent backend bootstrap:
    1) ensure DB exists
    2) ensure schema exists (migrations)
    3) seed scam_categories
    4) seed quiz data
    5) import open_dataset clean data
    6) generate missing embeddings
    """
    if os.getenv("DISABLE_AUTO_SEEDING", "").lower() in {"1", "true", "yes"}:
        print("[Seeding] Disabled by DISABLE_AUTO_SEEDING.")
        return

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SeedingError("DATABASE_URL is missing")

    params = _parse_database_url(db_url)
    await _ensure_database_exists(params)

    conn = await _connect(params)
    try:
        # Prevent concurrent duplicate seeding (important with multiple workers/replicas)
        await conn.execute("SELECT pg_advisory_lock($1)", SEEDING_LOCK_ID)

        # Make sure vector extension exists in this DB
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # 1) tables / migrations
        has_tables = await _has_any_business_tables(conn)
        if not has_tables:
            print("[Seeding] No business tables found. Running aerich upgrade...")
            await conn.close()
            await _run_aerich_upgrade()
            conn = await _connect(params)
            await conn.execute("SELECT pg_advisory_lock($1)", SEEDING_LOCK_ID)
        else:
            print("[Seeding] Tables already exist. Skip migration bootstrap step.")

        # 2) scam_categories
        scam_count = await _table_count(conn, "scam_categories")
        if scam_count == 0:
            print("[Seeding] scam_categories is empty. Seeding...")
            await conn.close()
            await _run_seed_scam_categories()
            conn = await _connect(params)
            await conn.execute("SELECT pg_advisory_lock($1)", SEEDING_LOCK_ID)
        else:
            print(f"[Seeding] scam_categories has {scam_count} rows. Skip.")

        # 3) quiz_questions + quiz_options
        qq_count = await _table_count(conn, "quiz_questions")
        qo_count = await _table_count(conn, "quiz_options")
        if qq_count == 0 and qo_count == 0:
            print("[Seeding] quiz tables are empty. Importing quiz SQL...")
            await _run_quiz_sql(conn)
        elif qq_count > 0 and qo_count > 0:
            print(
                f"[Seeding] quiz data exists (questions={qq_count}, options={qo_count}). Skip."
            )
        else:
            # Inconsistent partial data, do not blindly import to avoid PK conflict
            raise SeedingError(
                f"Inconsistent quiz data state: quiz_questions={qq_count}, quiz_options={qo_count}. "
                "Please clean/fix data before auto-seeding."
            )

        # 4) open_dataset
        open_count = await _table_count(conn, "open_dataset")
        if open_count == 0:
            print("[Seeding] open_dataset is empty. Importing clean data...")
            await conn.close()
            await _run_import_open_data()
            conn = await _connect(params)
            await conn.execute("SELECT pg_advisory_lock($1)", SEEDING_LOCK_ID)
        else:
            print(
                f"[Seeding] open_dataset has {open_count} rows. Skip clean-data import."
            )

        # 5) phishing_url
        phishing_count = await _table_count(conn, "phishing_url")
        if phishing_count == 0:
            print("[Seeding] phishing_url is empty. Importing clean URL data...")
            await conn.close()
            await _run_import_phishing_urls()
            conn = await _connect(params)
            await conn.execute("SELECT pg_advisory_lock($1)", SEEDING_LOCK_ID)
        else:
            print(
                f"[Seeding] phishing_url has {phishing_count} rows. Skip clean-url import."
            )

        # 6) embeddings (only missing rows)
        missing_embeddings = int(
            await conn.fetchval(
                "SELECT COUNT(*) FROM open_dataset WHERE text_embedding IS NULL"
            )
            or 0
        )
        missing_url_embeddings = int(
            await conn.fetchval(
                "SELECT COUNT(*) FROM phishing_url WHERE url_embedding IS NULL"
            )
            or 0
        )

        if missing_embeddings > 0 or missing_url_embeddings > 0:
            # change: for start backend container quickly,
            # seeding.py never calculates the vectors himself,
            # but leaves this hard labor to lifespan.py to run in the background.
            # await conn.close()
            # conn = await _connect(params)
            # await conn.execute("SELECT pg_advisory_lock($1)", SEEDING_LOCK_ID)
            print(
                f"[Seeding] Found missing embeddings: {missing_embeddings} text rows, {missing_url_embeddings} URL rows."
            )
            print(
                "[Seeding] Leaving embedding generation to background tasks in lifespan.py..."
            )
        else:
            print("[Seeding] All open_dataset rows already have embeddings. Skip.")

        print("[Seeding] Completed successfully.")
    finally:
        try:
            await conn.execute("SELECT pg_advisory_unlock($1)", SEEDING_LOCK_ID)
        except Exception:
            pass
        await conn.close()
