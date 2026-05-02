import asyncio
import os
import sys
import pandas as pd
from urllib.parse import urlparse
from tortoise import Tortoise
from dotenv import load_dotenv
import json
import csv

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
from app.core.config import settings


async def import_csv_to_db():
    print("[import phishing url] Initialize the database connection...")
    await Tortoise.init(config=TORTOISE_ORM)

    # 假设你把清洗好的 CSV 也放在 resources 文件夹下
    csv_path = os.path.join(project_root, "resources", "askvigil_50k_stratified.csv")
    # Use the computed property from your BaseSettings
    csv_path = settings.PHISH_CSV

    if not os.path.exists(csv_path):
        print(f"[import phishing url] Error: Data file not found {csv_path}")
        await Tortoise.close_connections()
        return

    print(f"[import phishing url] CSV data is being read: {csv_path}")
    try:
        df = pd.read_csv(
            csv_path,
            sep=',',
            # Default engine is fine now that we have the right file
            on_bad_lines='warn' 
        )
    except Exception as e:
        # A failure here means the file is fundamentally missing or locked
        raise RuntimeError(f"CRITICAL: Failed to load dataset schema. Error: {e}")
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
        # Use .get() with fallbacks to ensure no key errors
        is_mal = bool(row.get("is_malicious", True))
        raw_len = int(row.get("raw_length", 0))
        clean_len = int(row.get("clean_length", 0))
        
        # 1. Extraction (Standardized)
        raw_meta = row.get("metadata_vector")
        meta_list = None

        if isinstance(raw_meta, str) and raw_meta.strip():
            try:
                # Direct JSON parse. Pandas has already handled the CSV-level unquoting.
                meta_list = json.loads(raw_meta.strip())
            except (json.JSONDecodeError, TypeError):
                # Fallback for complex escaping or single-quote anomalies
                try:
                    import ast
                    meta_list = ast.literal_eval(raw_meta.strip())
                except:
                    meta_list = None
        elif isinstance(raw_meta, list):
            meta_list = raw_meta

        # 2. Hard Validation (Ensures the 8-dim Floor)
        if meta_list and isinstance(meta_list, list) and len(meta_list) == 8:
            validated_meta = [float(x) for x in meta_list]
        else:
            validated_meta = None
            # Log failures so we can track data quality without crashing the batch
            print(f"WARNING: ID {len(instances)} invalid metadata. Raw: {repr(raw_meta)}")
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
                raw_length=raw_len,      
                clean_length=clean_len,  
                source="open_dataset",
                metadata_vector=validated_meta
            )
        )

        # Temporary Debug within your for-loop
        if len(instances) > 49990 or len(instances) < 5:
            print(f"DEBUG: URL: {raw_url} | Meta Type: {type(meta_list)} | Content: {meta_list}")

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
