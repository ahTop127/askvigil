import onnxruntime as ort
from transformers import AutoTokenizer
from contextlib import asynccontextmanager
from fastapi import FastAPI

import os
import httpx
from pathlib import Path

# Global Registry
MODEL_REGISTRY = {}
# Define the Root of the data storage
CLOUD_STORAGE_URL = os.getenv("OCI_PAR_URL") # From environment
PERSISTENCE_ROOT = Path("/app/persistence").resolve()
# AI models subdirectory
BASE_MODEL_DIR = Path(PERSISTENCE_ROOT/"ai_models").resolve()
# Specific sub-paths
TEXT_MODEL_PATH = BASE_MODEL_DIR / "text_onnx"
URL_MODEL_PATH = BASE_MODEL_DIR / "url_onnx"


async def sync_assets():
    if not CLOUD_STORAGE_URL:
        raise RuntimeError("OCI_PAR_URL is missing!")

    async with httpx.AsyncClient(timeout=600.0) as client: # 10 min timeout for 237MB
        print(f"[Sync] Querying Oracle Bucket: {CLOUD_STORAGE_URL}", flush=True)
        list_resp = await client.get(CLOUD_STORAGE_URL)
        remote_files = list_resp.json().get('objects', [])
        print(f"[Sync] Found {len(remote_files)} objects in cloud.", flush=True)

        for obj in remote_files:
            name = obj['name']            
            # 1. Integrity Check: Skip directory placeholders (ending in /)
            if name.endswith('/'):
                continue

            local_path = PERSISTENCE_ROOT / name            
            size_bytes = obj.get('size', -1) # default to -1 if not found
            
            # 2. Logic: Only sync if missing or size mismatch
            if not local_path.exists() or (size_bytes != -1 and local_path.stat().st_size != size_bytes):                
                print(f"[Sync] Triggering download for: {name}", flush=True)                
                # Ensure the local directory structure exists
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Define a temporary path
                temp_path = local_path.with_suffix(".tmp")
                # Stream the download to the temporary file to save RAM 
                async with client.stream("GET", f"{CLOUD_STORAGE_URL}{name}") as response:
                    if response.status_code == 200:
                        with open(temp_path, "wb") as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                        # Finalizes the file only if the stream finished
                        temp_path.replace(local_path)
                        print(f"[Sync] Successfully saved {name}", flush=True)
                    else:
                        print(f"[Error] Failed to download {name}: {response.status_code}")
            else:
                print(f"[Cache] {name} is already up to date.", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Database sync 
    # The API will wait here until the download is finished
    print("[Lifespan] Starting asset synchronization...")
    await sync_assets()
    
    # 2. AI Preload - ONNX Inference Sessions (INT8)
    # Use 'CPUExecutionProvider' for ARM Neoverse N1
    providers = ['CPUExecutionProvider']
    
    print("[Lifespan] Loading Quantized ONNX Models...")
    MODEL_REGISTRY["text"] = {
        "session": ort.InferenceSession(TEXT_MODEL_PATH/"model_quantized.onnx", providers=providers),
        "tokenizer": AutoTokenizer.from_pretrained(
            str(TEXT_MODEL_PATH), 
            local_files_only=True,
            fix_mistral_regex=True 
        )
    }
    
    MODEL_REGISTRY["url"] = {
        "session": ort.InferenceSession(URL_MODEL_PATH/"model_quantized.onnx", providers=providers),
        "tokenizer": AutoTokenizer.from_pretrained(
            str(TEXT_MODEL_PATH), 
            local_files_only=True,
            fix_mistral_regex=True 
        )
    }

    yield
    # Shutdown logic
    MODEL_REGISTRY.clear()
    print("Models unloaded.")
