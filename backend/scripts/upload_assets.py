# Docker extension -> right click askvigil-backend, start new shell. then run:
# export PYTHONPATH=$PYTHONPATH:.
# uv run python -m scripts.upload_assets

# docker cp ./data_persistence/datasets/. askvigil-backend-1:/app/data_persistence/datasets/
# docker exec -it askvigil-backend-1 python /app/scripts/upload_assets.py
import os
from pathlib import Path

import httpx

# Use the same PAR URL from your .env
CLOUD_STORAGE_URL = os.getenv("OCI_PAR_URL")  # From environment


def upload_directory(local_path, remote_prefix):
    """
    Ensures local_path contents are uploaded under remote_prefix.
    Example:
    local_path: './text_onnx'
    remote_prefix: 'ai_models/text_onnx'
    Result: 'ai_models/text_onnx/model.onnx'
    """
    path = Path(local_path)
    remote_prefix = remote_prefix.strip("/")  # Remove trailing/leading slashes

    with httpx.Client(timeout=600.0) as client:
        # rglob("*") finds all files and subdirectories
        for file in path.rglob("*"):
            if file.is_file():
                # 1. Calculate path relative to the target folder itself
                # If file is ./text_onnx/sub/weights.bin, relative is sub/weights.bin
                inner_path = file.relative_to(path)

                # 2. Construct the full remote path
                remote_name = f"{remote_prefix}/{inner_path}".replace("\\", "/")

                print(f"Uploading {file} to {remote_name}...")

                with open(file, "rb") as f:
                    resp = client.put(f"{CLOUD_STORAGE_URL}{remote_name}", content=f)

                if resp.status_code == 200:
                    print("Success.")
                else:
                    print(f"Failed: {resp.status_code}")


if __name__ == "__main__":
    # Example usage:
    upload_directory("data_persistence/datasets", "datasets")
    upload_directory("data_persistence/ai_models/text_onnx", "ai_models/text_onnx")
    upload_directory("data_persistence/ai_models/url_onnx", "ai_models/url_onnx")
    upload_directory("data_persistence/ai_models/ocr_onnx", "ai_models/ocr_onnx")
