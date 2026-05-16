import asyncio
import os
import sys
from tortoise import Tortoise
from dotenv import load_dotenv
import gc

from app.core.database import TORTOISE_ORM
from app.models.open_data import OpenDataSet

# Introduce FastAPI and Lifespan (instead of directly introducing SentenceTransformer)
from app.core.registry import MODEL_REGISTRY
from app.services.nlp_service import get_onnx_embedding
import signal
import logging

logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
sys.path.append(project_root)

app_env = os.getenv("ENVIRONMENT", "dev")
env_filename = f".env.{app_env}"
env_path = os.path.join(project_root, env_filename)
if os.path.exists(env_path):
    load_dotenv(env_path)

# Add a global flag
keep_running = True


def handle_exit(sig, frame):
    """Enable graceful shutdown."""
    global keep_running
    logger.info("Shutdown signal received. Finishing current batch...")
    keep_running = False


# In your main execution logic
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)


async def manage_index(conn, action: str):
    """Lifecycle hook for HNSW indexing."""
    if action == "drop":
        logger.info(
            "--- [MAINTENANCE] Dropping HNSW Index for high-speed ingestion ---"
        )
        await conn.execute_query("DROP INDEX IF EXISTS idx_hnsw_embeddings;")

    elif action == "create":
        logger.info("--- [MAINTENANCE] Re-creating HNSW Index (Global Build) ---")
        # Note: This may take several minutes for 70k+ records
        await conn.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_hnsw_embeddings 
            ON open_dataset 
            USING hnsw (text_embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);
        """)
        logger.info("--- [MAINTENANCE] Indexing Complete ---")


async def generate_and_update_embeddings():
    # Create a virtual FastAPI instance to trigger lifespan
    # dummy_app = FastAPI()

    logger.info(
        "[TEXT] Triggering lifespan and loading the text model from the registry."
    )

    # 防止 generate_embeddings 进入 lifespan 后再次触发 run_seeding，导致递归子进程
    prev = os.environ.get("DISABLE_AUTO_SEEDING")
    os.environ["DISABLE_AUTO_SEEDING"] = "1"

    try:
        logger.info("Connect to the database...")

        # This piece of code is now running in the background of FastAPI
        # through asyncio.create_task() in lifespan.py.
        # It can no longer initialize or shut down the database by itself!

        conn = Tortoise.get_connection("default")

        total_count = await OpenDataSet.filter(text_embedding__isnull=True).count()
        if total_count == 0:
            logger.info("All text vectors already present.")
            return
        logger.info(f"Vectors missing for: {total_count} text data.")

        # PRE-INGESTION: Drop index to prevent CPU/Memory contention
        await manage_index(conn, "drop")

        # 3. Obtain model information from the global registry
        attempts = 0
        while "text" not in MODEL_REGISTRY:
            if attempts > 10:
                logger.exception(
                    "CRITICAL: Models timed out. Aborting background task."
                )
                return
            await asyncio.sleep(2)
            attempts += 1
            logger.info(f"Waiting for models... (Attempt {attempts})")

        # 4. Find all the data that has not yet generated vectors
        batch_size = 200
        offset = 0

        while keep_running:
            records = (
                await OpenDataSet.filter(text_embedding__isnull=True)
                .only("id", "clean_text")
                .limit(batch_size)
            )

            if not records:
                break

            # 5. Encode using the model obtained from the Registry
            texts = [
                record.clean_text if record.clean_text else "" for record in records
            ]
            embeddings = await get_onnx_embedding(
                texts, mode="text"
            )  # get from nlp_service.py

            for idx, record in enumerate(records):
                record.text_embedding = embeddings[idx].tolist()

            await OpenDataSet.bulk_update(
                records, fields=["text_embedding"], batch_size=batch_size
            )
            offset += len(records)
            if offset % 5000 == 0:
                logger.info(f"Progress: {offset} / {total_count}")
            # Garbage collection
            del records
            del texts
            del embeddings
            gc.collect()
            # Free up CPU time slices to reduce the risk of the system being occupied for a long time
            await asyncio.sleep(0.01)

        logger.info(
            "All text vectors have been generated! Database now ready for AI search!"
        )
    finally:
        if "total_count" in locals() and total_count > 0:
            await manage_index(conn, "create")

        if prev is None:
            os.environ.pop("DISABLE_AUTO_SEEDING", None)
        else:
            os.environ["DISABLE_AUTO_SEEDING"] = prev

    # After leaving the async with code block, lifespan will automatically execute the cleanup code following yield (MODEL_REGISTRY.clear()).


if __name__ == "__main__":
    # Exclusive independent running wrapper (only goes here when the terminal is manually executed)
    async def run_standalone():
        logger.info("[Standalone Mode] Initializing Database explicitly...")
        await Tortoise.init(config=TORTOISE_ORM)

        try:
            await generate_and_update_embeddings()
        finally:
            logger.info("[Standalone Mode] Closing database connections...")
            await Tortoise.close_connections()

    asyncio.run(run_standalone())
