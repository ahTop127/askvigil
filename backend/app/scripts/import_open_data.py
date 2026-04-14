import asyncio
import os
import sys
import pandas as pd
from tortoise import Tortoise
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"current_dir: {current_dir}")
app_dir = os.path.dirname(current_dir)
print(f"app_dir: {app_dir}")
project_root = os.path.dirname(app_dir)
print(f"project_root: {project_root}")
sys.path.append(project_root)

# 2. Dynamically load environment variables (must be loaded before importing core.database!)
# Read the system environment variable APP_ENV. If it is not set, it defaults to fallback to 'dev'.
app_env = os.getenv("ENVIRONMENT", "dev")
env_filename = f".env.{app_env}"
env_path = os.path.join(project_root, env_filename)

if os.path.exists(env_path):
    print(
        f" current runtime environment: {app_env.upper()}; configuration being loaded: {env_filename}"
    )
    load_dotenv(env_path)
else:
    print(
        f" Warning: The environment variable file {env_path} cannot be found. The system will attempt to rely on the existing system environment variables."
    )

from app.core.database import TORTOISE_ORM
from app.models.open_data import OpenDataSet


async def import_csv_to_db():
    print("Initialize the database connection...")
    await Tortoise.init(config=TORTOISE_ORM)

    # Dynamically calculate the absolute path of the CSV file (assuming your CSV is placed in the project root directory)
    # csv_path = os.path.join(project_root, "resources", "ready_for_db.csv")
    csv_path = os.path.join(project_root, "resources", "scam_dataset.csv")
    # csv_path = Path("data_persistence/datasets/scam_dataset.csv").resolve()

    if not os.path.exists(csv_path):
        print(f"Error: Data file not found {csv_path}")
        await Tortoise.close_connections()
        return

    print(f"CSV data is being read: {csv_path}")
    df = pd.read_csv(csv_path)

    # Convert the DataFrame to a list of dictionaries
    records = df.to_dict("records")

    print(f"Prepare to write the cleaned data of {len(records)} into PostgreSQL...")

    instances = [OpenDataSet(**row) for row in records]

    # Batch insertion
    await OpenDataSet.bulk_create(instances, batch_size=2000)

    print("The import has been completely completed! The basic data is ready.")

    # Close the connection
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(import_csv_to_db())
