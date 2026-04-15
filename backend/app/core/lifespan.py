import onnxruntime as ort
from transformers import AutoTokenizer
from contextlib import asynccontextmanager
from fastapi import FastAPI

import os
import httpx
from pathlib import Path

from app.core.seeding import run_seeding
from tortoise import Tortoise
from app.core.registry import MODEL_REGISTRY
from app.core.config import settings
from app.scripts.generate_embeddings import generate_and_update_embeddings
import asyncio


async def sync_assets():
    if not settings.OCI_PAR_URL:
        raise RuntimeError("OCI_PAR_URL is missing!")

    async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for 237MB
        print(f"[Sync] Querying Oracle Bucket: {settings.OCI_PAR_URL}", flush=True)
        list_resp = await client.get(settings.OCI_PAR_URL)
        remote_files = list_resp.json().get("objects", [])
        print(f"[Sync] Found {len(remote_files)} objects in cloud.", flush=True)

        for obj in remote_files:
            name = obj["name"]
            # 1. Integrity Check: Skip directory placeholders (ending in /)
            if name.endswith("/"):
                continue

            local_path = settings.PERSISTENCE_PATH / name
            size_bytes = obj.get("size", -1)  # default to -1 if not found

            # 2. Logic: Only sync if missing or size mismatch
            if not local_path.exists() or (
                size_bytes != -1 and local_path.stat().st_size != size_bytes
            ):
                print(f"[Sync] Triggering download for: {name}", flush=True)
                # Ensure the local directory structure exists
                local_path.parent.mkdir(parents=True, exist_ok=True)

                # Define a temporary path
                temp_path = local_path.with_suffix(".tmp")
                # Stream the download to the temporary file to save RAM
                async with client.stream(
                    "GET", f"{settings.OCI_PAR_URL}{name}"
                ) as response:
                    if response.status_code == 200:
                        with open(temp_path, "wb") as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                        # Finalizes the file only if the stream finished
                        temp_path.replace(local_path)
                        print(f"[Sync] Successfully saved {name}", flush=True)
                    else:
                        print(
                            f"[Error] Failed to download {name}: {response.status_code}"
                        )
            else:
                print(f"[Cache] {name} is already up to date.", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Database sync
    # The API will wait here until the download is finished
    print("[Lifespan] Starting asset synchronization...")
    await sync_assets()

    # Verify Schema
    await ensure_architectural_integrity()

    # 2. AI Preload - ONNX Inference Sessions (INT8)
    # Use 'ACLExecutionProvider' for ARM Neoverse N1

    print("[Lifespan] Loading Quantized ONNX Models...")
    try:
        # Load Text Model (MiniLM)
        MODEL_REGISTRY["text"] = {
            "session": load_onnx_session(str(settings.TEXT_MODEL_PATH)),
            "tokenizer": AutoTokenizer.from_pretrained(
                str(settings.TEXT_MODEL_PATH), local_files_only=True
            ),
        }

        MODEL_REGISTRY["text_classifier"] = {
            "session": load_onnx_session(str(settings.TEXT_CLASSIFIER_PATH))
        }

        # Load URL Model (URLBert)
        MODEL_REGISTRY["url"] = {
            "session": load_onnx_session(str(settings.URL_MODEL_PATH)),
            "tokenizer": AutoTokenizer.from_pretrained(
                str(settings.URL_MODEL_PATH), local_files_only=True
            ),
        }

        print("Models loaded successfully with SessionOptions(threads=1).")

    except Exception as e:
        print(f"CRITICAL: Failed to load models: {e}")
        raise e

    # Run seeding only after loading models
    # wangsi New addition: Perform database idempotent initialization before startup
    await run_seeding()
    # Note: We do NOT 'await' this. We fire and forget.
    os.environ["RUNNING_IN_APP"] = "1"
    asyncio.create_task(generate_and_update_embeddings())

    print("--- Server is LIVE. Background ingestion is running. ---")

    yield
    # Shutdown logic
    MODEL_REGISTRY.clear()
    print("Models unloaded.")


def load_onnx_session(model_path: str):
    """Encapsulated loader with ARM-specific optimizations."""
    options = ort.SessionOptions()
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

    # Match your docker-compose: Force 1 thread per operation
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1

    # Attempt ACL (Arm Compute Library) first, fallback to CPU
    providers = [
        ("ACLExecutionProvider", {"enable_fast_math": "True"}),
        "CPUExecutionProvider",
    ]

    p = Path(model_path)

    if p.is_dir():
        # It's a directory (MiniLM/URLBert) -> look for internal file
        target_file = p / "model_quantized.onnx"
    else:
        # It's a direct file (MLP Classifier) -> use it as is
        target_file = p

    if not target_file.exists():
        raise FileNotFoundError(f"ONNX binary not found at: {target_file}")

    # model_file = f"{model_path}/model_quantized.onnx"
    session = ort.InferenceSession(
        target_file, sess_options=options, providers=providers
    )

    # --- ACL CHECK ---
    active_providers = session.get_providers()
    if "ACLExecutionProvider" in active_providers:
        print(
            f"  [SUCCESS] {Path(model_path).name} loaded with ACL (Arm Compute Library)."
        )
    else:
        print(
            f"  [FALLBACK] {Path(model_path).name} using standard CPUExecutionProvider."
        )

    return session


async def ensure_architectural_integrity():
    """
    Synchronizes physical PG schema with architectural requirements.
    Prevents 'UndefinedColumn' errors caused by stale Docker volumes.
    """
    conn = Tortoise.get_connection("default")

    # 1. Extensions
    await conn.execute_script("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Column & Index Patching
    # We check each column individually to handle incremental updates to init.sql
    patch_sql = """
    DO $$ 
    BEGIN 
        -- Ensure columns exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='source') THEN
            ALTER TABLE open_dataset ADD COLUMN source VARCHAR(50);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='label') THEN
            ALTER TABLE open_dataset ADD COLUMN label VARCHAR(20);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='category') THEN
            ALTER TABLE open_dataset ADD COLUMN category VARCHAR(100);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='original_text') THEN
            ALTER TABLE open_dataset ADD COLUMN original_text TEXT;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='text_embedding') THEN
            ALTER TABLE open_dataset ADD COLUMN text_embedding vector(384);
        END IF;

        -- 1. Detection & Purge of Stale Config
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='open_dataset' AND column_name='text_search_vector'
        ) THEN
            IF (SELECT pg_get_expr(adbin, adrelid) 
                FROM pg_attrdef 
                JOIN pg_attribute ON pg_attrdef.adrelid = pg_attribute.attrelid AND pg_attrdef.adnum = pg_attribute.attnum
                WHERE adrelid = 'open_dataset'::regclass AND attname = 'text_search_vector') LIKE '%english%' THEN
                
                DROP INDEX IF EXISTS idx_gin_lexical;
                ALTER TABLE open_dataset DROP COLUMN text_search_vector;
            END IF;
        END IF;

        -- 2. State Enforcement (Simple Config)
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='text_search_vector') THEN
            ALTER TABLE open_dataset 
            ADD COLUMN text_search_vector tsvector 
            GENERATED ALWAYS AS (to_tsvector('simple', coalesce(clean_text, ''))) STORED;
        END IF;

        -- 3. Final Index Alignment
        CREATE INDEX IF NOT EXISTS idx_hnsw_embeddings 
            ON open_dataset USING hnsw (text_embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 128); -- Boosted for high-integrity retrieval

        CREATE INDEX IF NOT EXISTS idx_gin_lexical 
            ON open_dataset USING GIN (text_search_vector);

        RAISE NOTICE 'Architectural integrity check complete.';
    END $$;
    """

    try:
        await conn.execute_script(patch_sql)
        print("Schema synchronization successful.")
    except Exception as e:
        print(f"Schema sync failed: {str(e)}")
