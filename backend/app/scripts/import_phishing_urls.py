import asyncio
import os
import sys
import pandas as pd
from urllib.parse import urlparse
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
    print(
        f"[import phishing url] current runtime environment: {app_env.upper()}; configuration being loaded: {env_filename}"
    )
    load_dotenv(env_path)
else:
    print(
        f"[import phishing url] Warning: The environment variable file {env_path} cannot be found."
    )

from app.core.database import TORTOISE_ORM

# 替换为你的新 Model
from app.models.open_data import PhishingURL


async def import_csv_to_db():
    print("[import phishing url] Initialize the database connection...")
    await Tortoise.init(config=TORTOISE_ORM)

    # 假设你把清洗好的 CSV 也放在 resources 文件夹下
    csv_path = os.path.join(
        project_root, "resources", "askvigil_master_url_dataset.csv"
    )

    if not os.path.exists(csv_path):
        print(f"[import phishing url] Error: Data file not found {csv_path}")
        await Tortoise.close_connections()
        return

    print(f"[import phishing url] CSV data is being read: {csv_path}")
    df = pd.read_csv(csv_path)

    # Convert the DataFrame to a list of dictionaries
    records = df.to_dict("records")
    print(
        f"[import phishing url] Prepare to parse and write {len(records)} URLs into PostgreSQL..."
    )

    # --- 2. Add URL resolution logic ---
    instances = []
    for row in records:
        raw_url = str(row.get("url", ""))
        is_mal = bool(row.get("is_malicious", True))

        try:
            # Eliminate the parameters and extract the core domain name
            parsed = urlparse(raw_url)
            clean_domain = parsed.netloc
            clean_path = parsed.path
        except Exception:
            # The bad data that fails to be parsed is directly discarded
            continue

        instances.append(
            PhishingURL(
                original_url=raw_url,
                is_malicious=is_mal,
                domain=clean_domain,
                path=clean_path,
                source="open_dataset",  # Mark the source
            )
        )

    # --- 3. Batch warehousing ---
    print(f"[import phishing url] Batch creating {len(instances)} instances...")
    await PhishingURL.bulk_create(instances, batch_size=2000)

    print(
        "[import phishing url] The import has been completely completed! The URL basic data is ready."
    )

    # Close the connection
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(import_csv_to_db())
