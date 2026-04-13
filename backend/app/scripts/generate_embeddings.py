import asyncio
import os
import sys
from tortoise import Tortoise
from dotenv import load_dotenv
import numpy as np

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

            # Extract the true ONNX session/tokenizer
            tokenizer = model_info["tokenizer"]
            session = model_info["session"]
            print("Successfully obtained the model from the Registry!")

            print("Connect to the database...")
            await Tortoise.init(config=TORTOISE_ORM)
            db_inited = True

            # 4. Find all the data that has not yet generated vectors
            # batch_size = 1000
            batch_size = 50
            offset = 0

            total_count = await OpenDataSet.filter(text_embedding__isnull=True).count()
            print(
                f"It was found that a vector needs to be generated for the {total_count} data."
            )

            while True:
                records = await OpenDataSet.filter(text_embedding__isnull=True).limit(
                    batch_size
                )

                if not records:
                    break

                print(f"The next {len(records)} data entry is being processed...")

                # 5. Encode using the model obtained from the Registry
                # embeddings = model.encode(texts)
                texts = [
                    record.clean_text if record.clean_text else "" for record in records
                ]
                embeddings = await get_onnx_embedding(texts, mode="text") # get from nlp_service.py                

                for idx, record in enumerate(records):
                    record.text_embedding = embeddings[idx].tolist()

                await OpenDataSet.bulk_update(
                    records, fields=["text_embedding"], batch_size=50
                )

                # Free up CPU time slices to reduce the risk of the system being occupied for a long time
                await asyncio.sleep(0.1)

                offset += len(records)
                print(f"Progress: {offset} / {total_count}")

            print(
                "All vectors have been generated! Your database now has the ability of AI search!"
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



if __name__ == "__main__":
    asyncio.run(generate_and_update_embeddings())