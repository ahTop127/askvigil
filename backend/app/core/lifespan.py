import onnxruntime as ort
from transformers import AutoTokenizer
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

import os
import httpx
from pathlib import Path

from app.core.seeding import run_seeding
from tortoise import Tortoise
from app.core.registry import MODEL_REGISTRY
from app.core.config import settings
from app.scripts.generate_embeddings import generate_and_update_embeddings
from app.scripts.generate_url_embeddings import generate_and_update_url_embeddings
from rapidocr_onnxruntime import RapidOCR
import cv2
import multiprocessing
import onnxruntime as ort
import numpy as np

async def sync_assets():
    if not settings.OCI_PAR_URL:
        raise RuntimeError("OCI_PAR_URL is missing!")

    async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for 237MB
        print(f"[Sync] Querying Oracle Bucket: {settings.OCI_PAR_URL}", flush=True)
        list_resp = await client.get(settings.OCI_PAR_URL)
        remote_files = list_resp.json().get("objects", [])
        print(f"[Sync] Found {len(remote_files)} objects in cloud.", flush=True)

        for obj in remote_files:
            name = obj["name"]
            # 1. Integrity Check: Skip directory placeholders (ending in /)
            if name.endswith("/"):
                continue

            local_path = settings.PERSISTENCE_PATH / name
            size_bytes = obj.get("size", -1)  # default to -1 if not found

            # 2. Logic: Only sync if missing or size mismatch
            if not local_path.exists() or (
                size_bytes != -1 and local_path.stat().st_size != size_bytes
            ):
                print(f"[Sync] Triggering download for: {name}", flush=True)
                # Ensure the local directory structure exists
                local_path.parent.mkdir(parents=True, exist_ok=True)

                # Define a temporary path
                temp_path = local_path.with_suffix(".tmp")
                # Stream the download to the temporary file to save RAM
                async with client.stream(
                    "GET", f"{settings.OCI_PAR_URL}{name}"
                ) as response:
                    if response.status_code == 200:
                        with open(temp_path, "wb") as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                        # Finalizes the file only if the stream finished
                        temp_path.replace(local_path)
                        print(f"[Sync] Successfully saved {name}", flush=True)
                    else:
                        print(
                            f"[Error] Failed to download {name}: {response.status_code}"
                        )
            else:
                print(f"[Cache] {name} is already up to date.", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Database sync
    # The API will wait here until the download is finished
    print("[Lifespan] Starting asset synchronization...")
    await sync_assets()

    # Verify Schema
    await ensure_architectural_integrity()

    # 2. AI Preload - ONNX Inference Sessions (INT8)
    # Use 'CPUExecutionProvider' for ARM Neoverse N1 - ACL isn't actually better

    print("[Lifespan] Loading Quantized ONNX Models...")
    # try:
    try:
        # Load Text Model (MiniLM)
        MODEL_REGISTRY["text"] = {
            "session": load_onnx_session(str(settings.TEXT_MODEL_PATH)),
            "tokenizer": AutoTokenizer.from_pretrained(
                str(settings.TEXT_MODEL_PATH), local_files_only=True
            ),
        }
    except Exception as e:
        print(f"[MISSING MODEL] Text model not loaded: {e}")

    try:
        MODEL_REGISTRY["text_classifier"] = {
            "session": load_onnx_session(str(settings.TEXT_CLASSIFIER_PATH))
        }
    except Exception as e:
        print("[MISSING MODEL] Text classifier model not loaded: {e}")

    # Load URL Model (URLBert)
    try:
        MODEL_REGISTRY["url"] = {
            "session": load_onnx_session(str(settings.URL_MODEL_PATH)),
            "tokenizer": AutoTokenizer.from_pretrained(
                str(settings.URL_MODEL_PATH), local_files_only=True
            ),
        }
    except Exception as e:
        print("[MISSING MODEL] Url model not loaded: {e}")

    try:
        MODEL_REGISTRY["url_classifier"] = {
            "session": load_onnx_session(str(settings.URL_CLASSIFIER_PATH))
        }
    except Exception as e:
        print("[MISSING MODEL] Url classifier model not loaded: {e}")

    # --- OCR MODEL INITIALIZATION ---
    try:
        # --- THE RAPID PATH (Standard Fidelity / Efficiency) ---
        # Goal: Real-time inference on clean UI/Screenshots.
        # Optimized for the Ampere A1 by minimizing L3 cache pressure.
        MODEL_REGISTRY["ocr_rapid"] = RapidOCR(
            # 1. Model Paths
            det_model_path=str(settings.OCR_DET_RAPID_PATH),
            rec_model_path=str(settings.OCR_REC_RAPID_PATH),
            rec_keys_path=str(settings.OCR_KEYS_PATH),
            cls_model_path=None,             # Skip classification to save CPU cycles

            # 2. Engine & Hardware Optimization
            use_onnx=True,                   # Force ONNX Runtime backend
            intra_op_num_threads=4,          # Pin to physical core count (A1.Flex)
            rec_batch_num=4,                 # Cache-friendly batching (L2/L3 locality)
            
            # 3. Detection & Scaling
            det_limit_side_len=736,          # Area reduction: ~41% less math than 960px
            det_db_thresh=0.3,               # Balanced confidence threshold
            det_db_box_thresh=0.5,           # Filter noise; prioritize high-density text
            
            # 4. Post-Processing & Logic
            det_db_score_mode="fast",        # Optimization: Use perimeter-based scoring
            use_angle_cls=False,             # Disable angle check for UI-flat images
            use_textline_orientation=False,   # Assume standard horizontal layout
            use_space_char=False             # Standardize output for NLP service
        )
        print("[SUCCESS] OCR Rapid Engine loaded")
    except Exception as e:
        print(f"[MISSING MODEL] OCR Rapid Engine not loaded: {e}")

    try:
        # --- THE ENHANCED PATH (Forensic Fidelity / Integrity) ---
        # Goal: High-fidelity recovery for screen photos/distorted signals.
        # Uses 'server' weights to extract features from blur and glare.
        MODEL_REGISTRY["ocr_enhanced"] = RapidOCR(
            # 1. Model Paths
            # det_model_path=str(settings.OCR_DET_ENHANCED_PATH), # Accurate, but too slow
            det_model_path=str(settings.OCR_DET_RAPID_PATH), # Good enough even for enhanced
            rec_model_path=str(settings.OCR_REC_ENHANCED_PATH), # Thorough rec model
            rec_keys_path=str(settings.OCR_KEYS_PATH),
            cls_model_path=None,

            # 2. Engine & Hardware Optimization
            use_onnx=True,
            intra_op_num_threads=4,          # Match A1 architecture
            rec_batch_num=4,
            
            # 3. Detection & Forensic Scaling
            det_limit_side_len=960,     # Higher res for forensic detail
            det_db_thresh=0.3,          # DON'T reduce this, or it will just get noise
            det_db_box_thresh=0.5,      # Keep this standard to avoid noise
            det_db_unclip_ratio=1.6,    # Standard expansion
            
            # 4. Post-Processing & Logic
            det_db_score_mode="fast",
            use_angle_cls=False,
            use_textline_orientation=True,   # Forensic logic to handle tilted captures
            use_space_char=False
        )
        print("[SUCCESS] OCR Enhanced Engine loaded")
    except Exception as e:
        print(f"[MISSING MODEL] OCR Enhanced Engine not loaded: {e}")

    # Audit
    # --- [AUDIT] Enhanced Hardware Sync ---
    try:
        engine = MODEL_REGISTRY["ocr_rapid"]
        session = engine.text_rec.session
        # Correctly handle the RapidOCR wrapper
        actual_session = session.session if hasattr(session, 'session') else session
        model_neurons = actual_session.get_outputs()[0].shape[2]

        # Resolve RAM Truth
        active_vocab = engine.text_rec.postprocess_op.character
        ram_slots = len(active_vocab)

        # print(f"--- [DETAILED ALIGNMENT REPORT] ---")
        # print(f"[*] Model Neurons: {model_neurons}")
        # print(f"[*] RAM Slots:    {ram_slots}")
        
        # # Show Head and Tail
        # # We convert to list to ensure we can slice safely
        # vocab_list = list(active_vocab)
        # print(f"[*] HEAD (First 7): {vocab_list[:7]}")
        # print(f"[*] TAIL (Last 7):  {vocab_list[-7:]}")

        if model_neurons == ram_slots:
            # print(f"[√] DICT ALIGNMENT OK.") # Once verified, is expected
            pass
        else:
            print(f"[!] DICT MISMATCH: {model_neurons - ram_slots} difference.")
    except Exception as e:
        print(f"[!] Audit failed: {e}")

    # Run seeding only after loading models
    # wangsi New addition: Perform database idempotent initialization before startup
    await run_seeding()
    # Note: We do NOT 'await' this. We fire and forget.
    os.environ["RUNNING_IN_APP"] = "1"

    # # text contend embedding
    # asyncio.create_task(generate_and_update_embeddings())
    # # url phishing embedding
    # asyncio.create_task(generate_and_update_url_embeddings())

    # Create text and url embeddings sequentially (avoid OOM)
    asyncio.create_task(generate_embeddings_sequentially())

    print("--- Server is LIVE. Background ingestion is running. ---")
    cv2.setNumThreads(0) # Stop OpenCV thread competition    
    print(f"CPU Count: {multiprocessing.cpu_count()}")
    print(f"Available Providers: {ort.get_available_providers()}")
    # Inside your lifespan try-block, after initializing RapidOCR:
    dummy_img = np.zeros((320, 320, 3), dtype=np.uint8)
    for _ in range(2): # Run twice to ensure full graph optimization
        MODEL_REGISTRY["ocr_rapid"](dummy_img)
        MODEL_REGISTRY["ocr_enhanced"](dummy_img)
    print("[WARMUP] OCR Engines primed and ready")
    yield
    # Shutdown logic
    MODEL_REGISTRY.clear()
    print("Models unloaded.")


def load_onnx_session(model_path: str):
    """Encapsulated loader with ARM-specific optimizations."""
    options = ort.SessionOptions()
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

    # Intra = 4 maximizes single user speed. Is set in docker-compose now.
    # options.intra_op_num_threads = 4
    # options.inter_op_num_threads = 1

    # Use CPUExecutionProvider. ACL *not* used as it's not actually optimized for oracle a1
    providers = [        
        "CPUExecutionProvider",
    ]

    p = Path(model_path)

    if p.is_dir():
        # It's a directory (MiniLM/URLBert) -> look for internal file
        target_file = p / "model_quantized.onnx"
    else:
        # It's a direct file (MLP Classifier) -> use it as is
        target_file = p

    if not target_file.exists():
        raise FileNotFoundError(f"ONNX binary not found at: {target_file}")

    # model_file = f"{model_path}/model_quantized.onnx"
    session = ort.InferenceSession(
        target_file, sess_options=options, providers=providers
    )

    return session


async def ensure_architectural_integrity():
    """
    Synchronizes physical PG schema with architectural requirements.
    Prevents 'UndefinedColumn' errors caused by stale Docker volumes.
    """
    conn = Tortoise.get_connection("default")

    # 1. Extensions
    await conn.execute_script("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Column & Index Patching
    # We check each column individually to handle incremental updates to init.sql
    patch_sql = """
    DO $$ 
    BEGIN 
        -- Ensure columns exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='source') THEN
            ALTER TABLE open_dataset ADD COLUMN source VARCHAR(50);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='label') THEN
            ALTER TABLE open_dataset ADD COLUMN label VARCHAR(20);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='category') THEN
            ALTER TABLE open_dataset ADD COLUMN category VARCHAR(100);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='original_text') THEN
            ALTER TABLE open_dataset ADD COLUMN original_text TEXT;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='text_embedding') THEN
            ALTER TABLE open_dataset ADD COLUMN text_embedding vector(384);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='url_embedding') THEN
            ALTER TABLE open_dataset ADD COLUMN url_embedding vector(768);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='has_url') THEN
            ALTER TABLE open_dataset ADD COLUMN has_url SMALLINT DEFAULT 0;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='raw_length') THEN
            ALTER TABLE open_dataset ADD COLUMN raw_length INTEGER;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='clean_length') THEN
            ALTER TABLE open_dataset ADD COLUMN clean_length INTEGER;
        END IF;

        -- 1. Detection & Purge of Stale Config
        IF EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conname = 'open_dataset_clean_text_key'
        ) THEN
            ALTER TABLE open_dataset DROP CONSTRAINT open_dataset_clean_text_key;
        END IF;

        -- Ensure embeddings are stored as vector
        IF (SELECT data_type FROM information_schema.columns 
            WHERE table_name='open_dataset' AND column_name='text_embedding') != 'USER-DEFINED' THEN
            
            -- This forces the column to become a vector(384)
            ALTER TABLE open_dataset 
            ALTER COLUMN text_embedding TYPE vector(384) 
            USING text_embedding::vector(384);
        END IF;

        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='open_dataset' AND column_name='text_search_vector'
        ) THEN
            IF (SELECT pg_get_expr(adbin, adrelid) 
                FROM pg_attrdef 
                JOIN pg_attribute ON pg_attrdef.adrelid = pg_attribute.attrelid AND pg_attrdef.adnum = pg_attribute.attnum
                WHERE adrelid = 'open_dataset'::regclass AND attname = 'text_search_vector') LIKE '%english%' THEN
                
                DROP INDEX IF EXISTS idx_gin_lexical;
                ALTER TABLE open_dataset DROP COLUMN text_search_vector;
            END IF;
        END IF;

        -- 2. State Enforcement (Simple Config)
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='text_search_vector') THEN
            ALTER TABLE open_dataset 
            ADD COLUMN text_search_vector tsvector 
            GENERATED ALWAYS AS (to_tsvector('simple', coalesce(clean_text, ''))) STORED;
        END IF;

        -- 3. Final Index Alignment
        CREATE INDEX IF NOT EXISTS idx_hnsw_embeddings 
            ON open_dataset USING hnsw (text_embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);

        CREATE INDEX IF NOT EXISTS idx_gin_lexical 
            ON open_dataset USING GIN (text_search_vector);

        CREATE INDEX IF NOT EXISTS idx_open_dataset_metadata 
            ON open_dataset (source, has_url, raw_length, clean_length);

        -- Ensure phishing_url table exists (if not created by init.sql)
        CREATE TABLE IF NOT EXISTS phishing_url (id SERIAL PRIMARY KEY, original_url TEXT NOT NULL);        

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='phishing_url' AND column_name='resolved_url') THEN
            ALTER TABLE phishing_url ADD COLUMN resolved_url TEXT;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='source') THEN
            ALTER TABLE phishing_url ADD COLUMN source VARCHAR(50);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='is_malicious') THEN
            ALTER TABLE phishing_url ADD COLUMN is_malicious BOOLEAN DEFAULT TRUE;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='domain') THEN
            ALTER TABLE phishing_url ADD COLUMN domain VARCHAR(255);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='path') THEN
            ALTER TABLE phishing_url ADD COLUMN path TEXT;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='preview_title') THEN
            ALTER TABLE phishing_url ADD COLUMN preview_title VARCHAR(500);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='raw_length') THEN
            ALTER TABLE phishing_url ADD COLUMN raw_length INTEGER;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='clean_length') THEN
            ALTER TABLE phishing_url ADD COLUMN clean_length INTEGER;
        END IF;

        -- Audit timestamps
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='created_at') THEN
            ALTER TABLE phishing_url ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='updated_at') THEN
            ALTER TABLE phishing_url ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
        END IF;

        -- Ensure no unique constraint crashing db
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'phishing_url_original_url_key') THEN
            ALTER TABLE phishing_url DROP CONSTRAINT phishing_url_original_url_key;
        END IF;

        -- Ensure columns for phishing_url
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='url_embedding') THEN
            ALTER TABLE phishing_url ADD COLUMN url_embedding vector(768);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='metadata_vector') THEN
            ALTER TABLE phishing_url ADD COLUMN metadata_vector vector(8);
        END IF;

        -- 1. Check if the column exists AND if it's missing the fallback logic
        -- We check the column definition in the system catalogs
        IF EXISTS (
            SELECT 1 FROM pg_attribute 
            WHERE attrelid = 'phishing_url'::regclass 
            AND attname = 'url_search_vector'
        ) THEN
            -- If the formula doesn't mention 'original_url', it's the old version. Drop it.
            IF (SELECT pg_get_expr(adbin, adrelid) 
                FROM pg_attrdef 
                WHERE adrelid = 'phishing_url'::regclass 
                AND adnum = (SELECT attnum FROM pg_attribute WHERE attrelid = 'phishing_url'::regclass AND attname = 'url_search_vector')
            ) NOT LIKE '%original_url%' THEN
                
                ALTER TABLE phishing_url DROP COLUMN url_search_vector;
            END IF;
        END IF;

        -- 2. Create (or Re-create) with the robust fallback logic
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='url_search_vector') THEN
            ALTER TABLE phishing_url 
            ADD COLUMN url_search_vector tsvector 
            GENERATED ALWAYS AS (to_tsvector('simple', coalesce(preview_title, '')) || to_tsvector('simple', coalesce(resolved_url, original_url, ''))) STORED;
            
            CREATE INDEX IF NOT EXISTS idx_gin_url_lexical ON phishing_url USING GIN (url_search_vector);
        END IF;

        -- Final Index Alignment for phishing_url
        CREATE INDEX IF NOT EXISTS idx_hnsw_url_embeddings 
            ON phishing_url USING hnsw (url_embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);

        CREATE INDEX IF NOT EXISTS idx_gin_url_lexical 
            ON phishing_url USING GIN (url_search_vector);

        CREATE INDEX IF NOT EXISTS idx_phishing_url_metadata 
            ON phishing_url (source, domain, is_malicious);

        RAISE NOTICE 'Architectural integrity check complete.';
    END $$;
    """

    try:
        await conn.execute_script(patch_sql)
        print("Schema synchronization successful.")
    except Exception as e:
        print(f"Schema sync failed: {str(e)}")


async def generate_embeddings_sequentially():
    try:
        # Wait for the first to finish
        await generate_and_update_embeddings()
        # Only then start the second
        await generate_and_update_url_embeddings()
    except Exception as e:
        print(f"Embedding task failed: {e}")
