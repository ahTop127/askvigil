import asyncio
import sys
import pandas as pd
from tqdm import tqdm
from tortoise import Tortoise
from app.core.database import TORTOISE_ORM
from app.services.nlp_service import nlp_handler


async def run_import(file_path: str, category: str):
    # 1. Initialize DB Connection
    await Tortoise.init(config=TORTOISE_ORM)

    print(f"Reading {file_path}...")
    df = (
        pd.read_csv(file_path)
        if file_path.endswith(".csv")
        else pd.read_excel(file_path)
    )
    content_list = df["text"].dropna().astype(str).tolist()

    batch_size = 64

    # We use a raw connection for 'ON CONFLICT' because Tortoise's
    # high-level API doesn't support it natively for all dialects.
    conn = Tortoise.get_connection("default")

    for i in tqdm(
        range(0, len(content_list), batch_size), desc="Vectorizing & Uploading"
    ):
        batch_text = content_list[i : i + batch_size]
        # NLP Service handles the heavy lifting
        vectors = nlp_handler.model.encode(batch_text).tolist()

        for text_content, vec in zip(batch_text, vectors):
            # Raw SQL ensures simplicity for the UNIQUE constraint
            query = """
                INSERT INTO scam_embeddings (content, vector_data, category)
                VALUES (%s, %s, %s)
                ON CONFLICT (content) DO NOTHING;
            """
            await conn.execute_query(query, [text_content, vec, category])

    print(f"✅ Imported {len(content_list)} rows into {category}")
    await Tortoise.close_connections()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python import_data.py <file_path> <category>")
        sys.exit(1)
    asyncio.run(run_import(sys.argv[1], sys.argv[2]))
