import asyncio
import os
import sys
from tortoise import Tortoise
from dotenv import load_dotenv

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


async def generate_and_update_embeddings():
    # Create a virtual FastAPI instance to trigger lifespan
    dummy_app = FastAPI()

    print("The global lifecycle is being triggered and the AI model is being loaded from the Registry...")
    # Manually enter the lifespan context, which will load the model and store it in the MODEL_REGISTRY
    async with lifespan(dummy_app):

        # 3. Obtain model information from the global registry
        model_info = MODEL_REGISTRY.get("text_minilm")
        if not model_info:
            print("Error: The Text model failed to load in lifespan!")
            return

        # Extract the true SentenceTransformer model object
        model = model_info["model"]
        print(f"Successfully obtained the model from the Registry!")

        print("Connect to the database...")
        await Tortoise.init(config=TORTOISE_ORM)

        # 4. Find all the data that has not yet generated vectors
        batch_size = 1000
        offset = 0

        total_count = await OpenDataSet.filter(text_embedding__isnull=True).count()
        print(f"It was found that a vector needs to be generated for the {total_count} data.")

        while True:
            records = (
                await OpenDataSet.filter(text_embedding__isnull=True)
                .limit(batch_size)
                .offset(0)
            )

            if not records:
                break

            print(f"The next {len(records)} data entry is being processed...")

            texts = [record.clean_text if record.clean_text else "" for record in records]

            # 5. Encode using the model obtained from the Registry
            embeddings = model.encode(texts)

            for idx, record in enumerate(records):
                record.text_embedding = embeddings[idx].tolist()

            await OpenDataSet.bulk_update(
                records, fields=["text_embedding"], batch_size=500
            )

            offset += len(records)
            print(f"Progress: {offset} / {total_count}")

        print("All vectors have been generated! Your database now has the ability of AI search!")
        await Tortoise.close_connections()

    # After leaving the async with code block, lifespan will automatically execute the cleanup code following yield (MODEL_REGISTRY.clear()).
    print("When the life cycle ends, clear the memory.")


if __name__ == "__main__":
    asyncio.run(generate_and_update_embeddings())