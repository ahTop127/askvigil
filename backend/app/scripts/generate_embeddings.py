import asyncio
import os
import sys
from tortoise import Tortoise
from dotenv import load_dotenv
import numpy as np
import time

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
from app.models.open_data import OpenDataSet

# 2. Introduce FastAPI and Lifespan (instead of directly introducing SentenceTransformer)
from fastapi import FastAPI
from app.core.lifespan import lifespan, MODEL_REGISTRY
from app.services.nlp_service import get_onnx_embedding

def fast_vector_to_str(vector: np.ndarray) -> str:
    """Convert NumPy to pgvector string without heap bloating."""
    return "[" + ",".join(map(str, vector)) + "]"

async def generate_and_update_embeddings():
    # Create a virtual FastAPI instance to trigger lifespan
    dummy_app = FastAPI()

    print(
        "The global lifecycle is being triggered and the AI model is being loaded from the Registry..."
    )

    # 防止 generate_embeddings 进入 lifespan 后再次触发 run_seeding，导致递归子进程
    prev = os.environ.get("DISABLE_AUTO_SEEDING")
    os.environ["DISABLE_AUTO_SEEDING"] = "1"
    db_inited = False

    try:
        # Manually enter the lifespan context, which will load the model and store it in the MODEL_REGISTRY
        async with lifespan(dummy_app):
            # 3. Obtain model information from the global registry
            model_info = MODEL_REGISTRY.get("text")
            if not model_info:
                print("Error: The Text model failed to load in lifespan!")
                return

            # # Extract the true ONNX session/tokenizer
            # tokenizer = model_info["tokenizer"]
            # session = model_info["session"]
            # print("Successfully obtained the model from the Registry!")

            print("Connect to the database...")
            await Tortoise.init(config=TORTOISE_ORM)
            conn = Tortoise.get_connection("default")
            db_inited = True

            # 4. Find all the data that has not yet generated vectors
            # batch_size = 1000
            batch_size = 50
            offset = 0

            # total_count = await OpenDataSet.filter(text_embedding__isnull=True).count()
            # print(
            #     f"It was found that a vector needs to be generated for the {total_count} data."
            # )
            total_count = await conn.execute_query_dict(
                "SELECT COUNT(*) FROM open_dataset WHERE text_embedding IS NULL"
            )
            total_count = total_count[0]['count']
            
            print(f"Vectors need to be generated for: {total_count} records.")
            global_start = time.perf_counter()

            while True:
                # Query only the raw ID and Text to keep the Python heap slim
                records = await conn.execute_query_dict(
                    "SELECT id, clean_text FROM open_dataset WHERE text_embedding IS NULL LIMIT %s",
                    [batch_size]
                )
                # records = await OpenDataSet.filter(text_embedding__isnull=True).limit(
                #     batch_size
                # )

                if not records:
                    break
                batch_start = time.perf_counter()

                print(f"The next {len(records)} data entry is being processed...")

                # 5. Encode using the model obtained from the Registry
                # embeddings = model.encode(texts)

                # 1. Generate embeddings with central service
                texts = [r["clean_text"] for r in records]
                embeddings = await get_onnx_embedding(texts, mode="text")
                # texts = [
                #     record.clean_text if record.clean_text else "" for record in records
                # ]
                # embeddings = encode_texts_with_onnx(texts, tokenizer, session)

                # 2. Construct the Batch VALUES list
                # We use %s placeholders to maintain SQL security
                values_placeholders = []
                flat_params = []
                
                for idx, record in enumerate(records):
                    # record.text_embedding = embeddings[idx].tolist()
                    
                    v_str = fast_vector_to_str(embeddings[idx])
                    values_placeholders.append("(%s, %s::vector)")
                    flat_params.extend([record["id"], v_str])

                # 3. The "Institutional" Batch Update
                sql = f"""
                    UPDATE open_dataset AS o
                    SET text_embedding = v.vec
                    FROM (VALUES {", ".join(values_placeholders)}) AS v(id, vec)
                    WHERE v.id = o.id;
                """
                
                # Execute one single round-trip
                await conn.execute_query(sql, flat_params)

                # for idx, record in enumerate(records):
                #     record.text_embedding = embeddings[idx].tolist()

                # await OpenDataSet.bulk_update(
                #     records, fields=["text_embedding"], batch_size=50
                # )

                # -------------------------
                batch_end = time.perf_counter()

                # --- TELEMETRY CALCULATIONS ---
                offset += len(records)
                batch_time = batch_end - batch_start
                total_elapsed = batch_end - global_start
                
                items_per_sec = len(records) / batch_time
                avg_items_per_sec = offset / total_elapsed
                ms_per_item = (batch_time / len(records)) * 1000

                print(
                    f"[{offset}/{total_count}] | "
                    f"Batch: {items_per_sec:.1f} it/s ({ms_per_item:.2f} ms/it) | "
                    f"Avg: {avg_items_per_sec:.1f} it/s | "
                    f"Elapsed: {total_elapsed:.1f}s"
                )
                # -------------------------
                # Free up CPU time slices to reduce the risk of the system being occupied for a long time
                await asyncio.sleep(0.1)

                # offset += len(records)
                # print(f"Progress: {offset} / {total_count}")

            print(
                f"\nGenerated all vectors for AI search in {time.perf_counter() - global_start:.2f}s"
            )
    finally:
        # 先关闭 DB（如果已初始化）
        if db_inited:
            await Tortoise.close_connections()

        # 再恢复环境变量
        if prev is None:
            os.environ.pop("DISABLE_AUTO_SEEDING", None)
        else:
            os.environ["DISABLE_AUTO_SEEDING"] = prev

    # After leaving the async with code block, lifespan will automatically execute the cleanup code following yield (MODEL_REGISTRY.clear()).
    print("When the life cycle ends, clear the memory.")


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
    return np.sum(token_embeddings * input_mask_expanded, 1) / np.clip(
        input_mask_expanded.sum(1), a_min=1e-9, a_max=None
    )


def encode_texts_with_onnx(texts: list[str], tokenizer, session) -> np.ndarray:
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="np",
    )
    outputs = session.run(None, dict(encoded))
    # text model 用 mean pooling
    return mean_pooling(outputs, encoded["attention_mask"])


if __name__ == "__main__":
    asyncio.run(generate_and_update_embeddings())
