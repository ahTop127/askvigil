# Docker extension -> right click askvigil-backend, start new shell. then run:
# export PYTHONPATH=$PYTHONPATH:.
# uv run python -m scripts.upload_assets
import os
import httpx
from pathlib import Path

# Use the same PAR URL from your .env
CLOUD_STORAGE_URL = os.getenv("OCI_PAR_URL") # From environment

def upload_directory(local_path, remote_prefix):
    """
    local_path: 'local_models/text_model'
    remote_prefix: 'ai_models/text_model'
    """
    path = Path(local_path)
    
    with httpx.Client(timeout=600.0) as client:
        for file in path.rglob("*"): # Recursive glob to find all files
            if file.is_file():
                # Construct the remote path
                relative_path = file.relative_to(path.parent)
                remote_name = str(relative_path).replace("\\", "/") # Ensure Linux-style paths
                
                print(f"Uploading {file} to {remote_name}...")
                
                with open(file, "rb") as f:
                    resp = client.put(f"{CLOUD_STORAGE_URL}{remote_name}", content=f)
                
                if resp.status_code == 200:
                    print("Success.")
                else:
                    print(f"Failed: {resp.status_code}")

if __name__ == "__main__":
    # Example usage:
    upload_directory("./text_model", "ai_models/text_model")