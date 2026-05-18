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
from app.database_init.generate_embeddings import generate_and_update_embeddings
from app.database_init.generate_url_embeddings import generate_and_update_url_embeddings
from app.services.nlp_service import get_onnx_embedding
from rapidocr_onnxruntime import RapidOCR
import cv2
import numpy as np
import joblib
import logging

logger = logging.getLogger(__name__)


async def sync_assets():
    if not settings.OCI_PAR_URL:
        raise RuntimeError("OCI_PAR_URL is missing!")

    async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for 237MB
        logger.info("[Sync] Querying Oracle Bucket")
        list_resp = await client.get(settings.OCI_PAR_URL)
        remote_files = list_resp.json().get("objects", [])
        logger.info(f"[Sync] Found {len(remote_files)} objects in cloud.")

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
                logger.info(f"[Sync] Triggering download for: {name}")
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
                        logger.info(f"[Sync] Successfully saved {name}")
                    else:
                        logger.exception(
                            f"[Error] Failed to download {name}: {response.status_code}"
                        )
            else:
                logger.info(f"[Cache] {name} is already up to date.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Database sync
    # The API will wait here until the download is finished
    logger.info("[Lifespan] Starting asset synchronization...")
    await sync_assets()

    # Verify Schema
    await ensure_architectural_integrity()

    # 2. AI Preload - ONNX Inference Sessions (INT8)
    # Use 'CPUExecutionProvider' for ARM Neoverse N1 - ACL isn't actually better

    logger.info("[Lifespan] Loading Quantized ONNX Models...")
    try:
        # Load Text Model (MiniLM)
        MODEL_REGISTRY["text"] = {
            "session": load_onnx_session(str(settings.TEXT_MODEL_PATH)),
            "tokenizer": AutoTokenizer.from_pretrained(
                str(settings.TEXT_MODEL_PATH), local_files_only=True
            ),
        }
    except Exception as e:
        logger.exception(f"[MISSING MODEL] Text model not loaded: {e}")

    # XGB
    try:
        MODEL_REGISTRY["text_classifier"] = {
            "session": joblib.load(settings.TEXT_CLASSIFIER_PATH)
        }
    except Exception as e:
        logger.exception(f"[MISSING MODEL] Text classifier model not loaded: {e}")

    # Load URL Model (URLBert)
    try:
        MODEL_REGISTRY["url"] = {
            "session": load_onnx_session(str(settings.URL_MODEL_PATH)),
            "tokenizer": AutoTokenizer.from_pretrained(
                str(settings.URL_MODEL_PATH), local_files_only=True
            ),
        }
    except Exception:
        logger.exception("[MISSING MODEL] Url model not loaded: {e}")

    # XGB
    try:
        MODEL_REGISTRY["url_classifier"] = {
            "session": joblib.load(settings.URL_CLASSIFIER_PATH)
        }
    except Exception as e:
        logger.exception(f"[MISSING MODEL] Text classifier model not loaded: {e}")

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
            cls_model_path=None,  # Skip classification to save CPU cycles
            # 2. Engine & Hardware Optimization
            use_onnx=True,  # Force ONNX Runtime backend
            intra_op_num_threads=4,  # Pin to physical core count (A1.Flex)
            rec_batch_num=4,  # Cache-friendly batching (L2/L3 locality)
            # 3. Detection & Scaling
            det_limit_side_len=736,  # Area reduction: ~41% less math than 960px
            det_db_thresh=0.3,  # Balanced confidence threshold
            det_db_box_thresh=0.5,  # Filter noise; prioritize high-density text
            # 4. Post-Processing & Logic
            det_db_score_mode="fast",  # Optimization: Use perimeter-based scoring
            use_angle_cls=False,  # Disable angle check for UI-flat images
            use_textline_orientation=False,  # Assume standard horizontal layout
            use_space_char=False,  # Standardize output for NLP service
        )
        logger.info("[SUCCESS] OCR Rapid Engine loaded")
    except Exception as e:
        logger.info(f"[MISSING MODEL] OCR Rapid Engine not loaded: {e}")

    try:
        # --- THE ENHANCED PATH (Forensic Fidelity / Integrity) ---
        # Goal: High-fidelity recovery for screen photos/distorted signals.
        # Uses 'server' weights for recognition to extract features from blur and glare.
        # NOTE: Using the RAPID model for text detection. The ENHANCED model 
        # (settings.OCR_DET_ENHANCED_PATH) is more accurate but suffers from 
        # severe latency bottlenecks in production.
        MODEL_REGISTRY["ocr_enhanced"] = RapidOCR(
            # 1. Model Paths
            det_model_path=str(
                settings.OCR_DET_RAPID_PATH
            ),  # Good enough even for enhanced
            rec_model_path=str(settings.OCR_REC_ENHANCED_PATH),  # Thorough rec model
            rec_keys_path=str(settings.OCR_KEYS_PATH),
            cls_model_path=None,
            # 2. Engine & Hardware Optimization
            use_onnx=True,
            intra_op_num_threads=4,  # Match A1 architecture
            rec_batch_num=4,
            # 3. Detection & Forensic Scaling
            det_limit_side_len=960,  # Higher res for forensic detail
            det_db_thresh=0.3,  # DON'T reduce this, or it will just get noise
            det_db_box_thresh=0.5,  # Keep this standard to avoid noise
            det_db_unclip_ratio=1.6,  # Standard expansion
            # 4. Post-Processing & Logic
            det_db_score_mode="fast",
            use_angle_cls=False,
            use_textline_orientation=True,  # Forensic logic to handle tilted captures
            use_space_char=False,
        )
        logger.info("[SUCCESS] OCR Enhanced Engine loaded")
    except Exception as e:
        logger.exception(f"[MISSING MODEL] OCR Enhanced Engine not loaded: {e}")

    # Audit
    # --- [AUDIT] Enhanced Hardware Sync ---
    try:
        engine = MODEL_REGISTRY["ocr_rapid"]
        session = engine.text_rec.session
        # Correctly handle the RapidOCR wrapper
        actual_session = session.session if hasattr(session, "session") else session
        model_neurons = actual_session.get_outputs()[0].shape[2]

        # Resolve RAM Truth
        active_vocab = engine.text_rec.postprocess_op.character
        ram_slots = len(active_vocab)

        if model_neurons == ram_slots:
            logger.info("[√] DICT ALIGNMENT OK.")  # Once verified, is expected
        else:
            logger.exception(
                f"[!] DICT MISMATCH: {model_neurons - ram_slots} difference."
            )
    except Exception as e:
        logger.exception(f"[!] Audit failed: {e}")

    # Run seeding only after loading models
    # Perform database idempotent initialization before startup
    await run_seeding()
    os.environ["RUNNING_IN_APP"] = "1"

    # Create text and url embeddings sequentially (avoid OOM).
    # Do NOT await this, fire on forget so server runs while generating embeddings
    asyncio.create_task(generate_embeddings_sequentially())

    logger.info("--- Server is LIVE. Background ingestion is running. ---")
    cv2.setNumThreads(0)  # Stop OpenCV thread competition

    # Warm up to avoid slow first inference
    await warm_up_engines()

    yield
    # Shutdown logic
    MODEL_REGISTRY.clear()
    logger.info("Models unloaded.")


async def warm_up_engines():
    """
    Prevents the 5-second 'Cold Start' by pre-allocating ONNX tensors
    and triggering the C++ backends before the first user request.
    """
    logger.info("[INIT] Warming up Inference Engines on ARM64...")
    # 1. Saturate the Transformer (ONNX)
    # We do this 3 times to ensure the graph optimizer finishes kernel selection
    for i in range(3):
        await get_onnx_embedding("warmup text for saturation", mode="text")
        await get_onnx_embedding("https://warmup-url.com/saturate", mode="url")
    logger.info("[WARMUP] Transformer saturated.")

    # 2. Saturate the XGBoost Classifier
    # XGBoost boosters often lazy-load tree structures on the first few passes
    dummy_input_text = np.zeros((1, 384), dtype=np.float32)
    dummy_input_url = np.zeros((1, 776), dtype=np.float32)  # Embedding + Metadata

    for i in range(3):
        MODEL_REGISTRY["text_classifier"]["session"].predict_proba(dummy_input_text)
        MODEL_REGISTRY["url_classifier"]["session"].predict_proba(dummy_input_url)
    logger.info("[WARMUP] Classifiers saturated.")

    # 3. Saturate the OCR (The Heaviest Lift)
    # RapidOCR actually has THREE internal models (Det, Rec, Cls).
    # It takes several passes to stabilize the memory pool for all three.
    dummy_img = np.zeros(
        (640, 640, 3), dtype=np.uint8
    )  # Use 640x640 to trigger real padding logic
    for i in range(5):  # OCR is finicky, give it 5 passes
        MODEL_REGISTRY["ocr_rapid"](dummy_img)
        MODEL_REGISTRY["ocr_enhanced"](dummy_img)
    logger.info("[WARMUP] OCR saturated.")
    logger.info("[INIT] System is ready. All caches primed.")


def load_onnx_session(model_path: str):
    """Encapsulated loader with ARM-specific optimizations."""
    options = ort.SessionOptions()
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

    # Maximizes single user speed by using all intra threads available.
    # Fallback to 4 if the Docker Compose environment variable isn't detected
    intra_threads = int(os.getenv("ONNXRUNTIME_INTRA_OP_NUM_THREADS", "4"))
    inter_threads = int(os.getenv("ONNXRUNTIME_INTER_OP_NUM_THREADS", "1"))

    # Explicitly bind ONNX engine threading to match container boundaries
    options.intra_op_num_threads = intra_threads
    options.inter_op_num_threads = inter_threads

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

    session = ort.InferenceSession(
        target_file, sess_options=options, providers=providers
    )

    return session


async def ensure_architectural_integrity():
    """
    Synchronizes physical PG schema with architectural requirements.
    Prevents 'UndefinedColumn' errors caused by stale Docker volumes.
    """
    # INCREMENT THIS whenever you add a new migration block below
    CURRENT_SCHEMA_VERSION = 2
    conn = Tortoise.get_connection("default")

    # 1. Extensions
    await conn.execute_script("""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
    """)

    # 2: Ensure the "Tracker" exists (Very fast)
    await conn.execute_script("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INT PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 3. Quick Check
    result = await conn.execute_query_dict(
        "SELECT MAX(version) as v FROM schema_version"
    )
    db_version = result[0]["v"] or 0

    if db_version >= CURRENT_SCHEMA_VERSION:
        return  # Instant exit if we're up to date

    # 4. Migrations
    logger.info(
        f"[DB MIGRATION] Migrating database from v{db_version} to v{CURRENT_SCHEMA_VERSION}..."
    )

    # 4. Column & Index Patching (Slow and heavy)
    patch_sql = """
    DO $$ 
    BEGIN 
        -- ==========================================
        -- PHASE 1: CLEANUP OLD TSVECTOR SYSTEM
        -- ==========================================
        
        -- Drop old GIN indexes
        DROP INDEX IF EXISTS idx_gin_lexical;
        DROP INDEX IF EXISTS idx_gin_url_lexical;

        -- Drop the massive generated text columns
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='text_search_vector') THEN
            ALTER TABLE open_dataset DROP COLUMN text_search_vector;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='url_search_vector') THEN
            ALTER TABLE phishing_url DROP COLUMN url_search_vector;
        END IF;

        -- ==========================================
        -- PHASE 2: ENSURE BASE COLUMNS EXIST
        -- ==========================================
        
        -- open_dataset checks
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
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='has_url') THEN
            ALTER TABLE open_dataset ADD COLUMN has_url SMALLINT DEFAULT 0;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='raw_length') THEN
            ALTER TABLE open_dataset ADD COLUMN raw_length INTEGER;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='clean_length') THEN
            ALTER TABLE open_dataset ADD COLUMN clean_length INTEGER;
        END IF;

        -- Ensure embeddings are stored as vector
        IF (SELECT data_type FROM information_schema.columns WHERE table_name='open_dataset' AND column_name='text_embedding') != 'USER-DEFINED' THEN
            ALTER TABLE open_dataset ALTER COLUMN text_embedding TYPE vector(384) USING text_embedding::vector(384);
        END IF;

        -- phishing_url checks
        CREATE TABLE IF NOT EXISTS phishing_url (id SERIAL PRIMARY KEY, original_url TEXT NOT NULL);        

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='resolved_url') THEN
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
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='url_embedding') THEN
            ALTER TABLE phishing_url ADD COLUMN url_embedding vector(768);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='metadata_vector') THEN
            ALTER TABLE phishing_url ADD COLUMN metadata_vector vector(8);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='created_at') THEN
            ALTER TABLE phishing_url ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='phishing_url' AND column_name='updated_at') THEN
            ALTER TABLE phishing_url ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
        END IF;

        -- ==========================================
        -- PHASE 3: APPLY NEW INDEXES (HNSW + TRIGRAM)
        -- ==========================================

        -- open_dataset Indexes
        CREATE INDEX IF NOT EXISTS idx_hnsw_embeddings 
            ON open_dataset USING hnsw (text_embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);

        CREATE INDEX IF NOT EXISTS idx_open_dataset_metadata 
            ON open_dataset (source, has_url, raw_length, clean_length);

        CREATE INDEX IF NOT EXISTS idx_trgm_clean_text 
            ON open_dataset USING GIN (clean_text gin_trgm_ops);

        -- phishing_url Indexes
        CREATE INDEX IF NOT EXISTS idx_hnsw_url_embeddings 
            ON phishing_url USING hnsw (url_embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);

        CREATE INDEX IF NOT EXISTS idx_phishing_url_metadata 
            ON phishing_url (source, domain, is_malicious);

        CREATE INDEX IF NOT EXISTS idx_trgm_url 
            ON phishing_url USING GIN ((coalesce(resolved_url, original_url)) gin_trgm_ops);

        RAISE NOTICE 'Architectural integrity check complete. Trigram system active.';
    END $$;
    """

    try:
        await conn.execute_script(patch_sql)
        # 4. Mark as complete
        await conn.execute_script(
            f"INSERT INTO schema_version (version) VALUES ({CURRENT_SCHEMA_VERSION});"
        )
        logger.info(f"Schema synchronization to v{CURRENT_SCHEMA_VERSION} successful.")
    except Exception as e:
        logger.info(f"Schema sync failed: {str(e)}")


async def generate_embeddings_sequentially():
    try:
        # Wait for the first to finish
        await generate_and_update_embeddings()
        # Only then start the second
        await generate_and_update_url_embeddings()
    except Exception as e:
        logger.info(f"Embedding task failed: {e}")
