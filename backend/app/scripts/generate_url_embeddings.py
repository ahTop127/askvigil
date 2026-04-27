import asyncio
import os
import sys
from tortoise import Tortoise
from dotenv import load_dotenv
import gc

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
sys.path.append(project_root)

app_env = os.getenv("ENVIRONMENT", "dev")
env_filename = f".env.{app_env}"
env_path = os.path.join(project_root, env_filename)
if os.path.exists(env_path):
    load_dotenv(env_path)

from app.core.database import TORTOISE_ORM
from app.models.open_data import PhishingURL

from app.core.registry import MODEL_REGISTRY
from app.services.nlp_service import get_onnx_embedding
import signal

# Add a global flag
keep_running = True


def handle_exit(sig, frame):
    """Enable graceful shutdown."""
    global keep_running
    print("Shutdown signal received. Finishing current batch...")
    keep_running = False


# In your main execution logic
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)


async def manage_url_index(conn, action: str):
    """Lifecycle hook for HNSW indexing (URL Vectors)."""
    # 2. Note: The index name here must be distinguished from the index name of text, for example, idx_hnsw_url_embeddings
    if action == "drop":
        print("--- [MAINTENANCE] Dropping URL HNSW Index for high-speed ingestion ---")
        await conn.execute_query("DROP INDEX IF EXISTS idx_hnsw_url_embeddings;")

    elif action == "create":
        print("--- [MAINTENANCE] Re-creating URL HNSW Index (Global Build) ---")
        # 对应 phishing_url 表和 url_embedding 字段
        await conn.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_hnsw_url_embeddings 
            ON phishing_url 
            USING hnsw (url_embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);
        """)
        print("--- [MAINTENANCE] URL Indexing Complete ---")


async def generate_and_update_url_embeddings():
    print(
        "[embedding phishing url] URL Embedding lifecycle is being triggered and waiting for the AI model from Registry..."
    )

    prev = os.environ.get("DISABLE_AUTO_SEEDING")
    os.environ["DISABLE_AUTO_SEEDING"] = "1"
    # db_inited = False

    try:
        print("[embedding phishing url] Connect to the database...")

        # This piece of code is now running in the background of FastAPI
        # through asyncio.create_task() in lifespan.py.
        # It can no longer initialize or shut down the database by itself!
        # await Tortoise.init(config=TORTOISE_ORM)
        # conn = Tortoise.get_connection("default")
        # db_inited = True
        conn = Tortoise.get_connection("default")

        # PRE-INGESTION: Drop index
        await manage_url_index(conn, "drop")

        # 3. Obtain the URL model from the global Registry (wait for the lifespan initialization to complete)
        attempts = 0
        while "url" not in MODEL_REGISTRY:
            if attempts > 10:
                print(
                    "[embedding phishing url] CRITICAL: URL Model timed out. Aborting background task."
                )
                return
            await asyncio.sleep(2)
            attempts += 1
            print(
                f"[embedding phishing url] Waiting for URL model... (Attempt {attempts})"
            )

        # 4. Search for URL data where no vector has been generated
        batch_size = 200
        offset = 0

        total_count = await PhishingURL.filter(url_embedding__isnull=True).count()
        print(
            f"[embedding phishing url] Found {total_count} URL data entries needing embeddings."
        )

        if total_count == 0:
            print("[embedding phishing url] All URL vectors are already up-to-date.")
            return

        while keep_running:  # Allow graceful shut down
            # Only take the necessary fields to reduce memory usage
            records = (
                await PhishingURL.filter(url_embedding__isnull=True)
                .only("id", "original_url", "resolved_url")
                .limit(batch_size)
            )

            if not records:
                break

            print(
                f"[embedding phishing url] Processing next batch of {len(records)} URLs..."
            )

            # 5. Extract the urls that truly require Embedding
            # We use the resolved_url if we have it (from real-time scans),
            # otherwise we use the original_url (the raw bit.ly or scam link).
            target_urls = [
                record.resolved_url
                if (record.resolved_url and record.resolved_url.strip())
                else record.original_url
                for record in records
            ]

            # Call the underlying ONNX service (note that mode="url")
            embeddings = await get_onnx_embedding(target_urls, mode="url")

            for idx, record in enumerate(records):
                record.url_embedding = embeddings[idx].tolist()

            # Update to the database
            await PhishingURL.bulk_update(
                records, fields=["url_embedding"], batch_size=batch_size
            )
            offset += len(records)
            print(f"[embedding phishing url] URL Progress: {offset} / {total_count}")

            # Garbage collection and time slice concession
            del records
            del target_urls
            del embeddings
            gc.collect()
            await asyncio.sleep(0.01)

        print(
            "[embedding phishing url] All URL vectors have been generated successfully!"
        )

    finally:
        # if db_inited:
        #     # POST-INGESTION: 建回 HNSW 索引
        #     await manage_url_index(conn, "create")
        #     await Tortoise.close_connections()

        await manage_url_index(conn, "create")

        if prev is None:
            os.environ.pop("DISABLE_AUTO_SEEDING", None)
        else:
            os.environ["DISABLE_AUTO_SEEDING"] = prev

    print("[embedding phishing url] URL Embedding task memory cleared.")


if __name__ == "__main__":
    # Exclusive independent operation wrapper
    async def run_standalone():
        print("[Standalone Mode] Initializing Database explicitly...")
        await Tortoise.init(config=TORTOISE_ORM)

        try:
            await generate_and_update_url_embeddings()
        finally:
            print("[Standalone Mode] Closing database connections...")
            await Tortoise.close_connections()

    # You will only go here when you manually execute the python script in the terminal
    asyncio.run(run_standalone())
