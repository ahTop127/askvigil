# docker exec -it -e PYTHONPATH="/app" askvigil-backend-1 python /app/scripts/train-xgb-heads.py
import random
import asyncio
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator

from xgboost import XGBClassifier

from tortoise import Tortoise

from app.core.config import settings
from app.core.database import TORTOISE_ORM
from app.models.open_data import OpenDataSet, PhishingURL


# ======================================================================
# DATASET PREPARATION
# ======================================================================

class StratifiedDataset:
    """
    Mirrors PyTorch logic but optimized for tree-based estimators.
    1. Buckets by text length to prevent length-based bias.
    2. Enforces strict 1:1 class balancing per bucket.
    3. Flattens embeddings (and optional metadata) into a 1D feature array.
    """

    def __init__(
        self,
        haz_records,
        safe_records,
        attr_name,
        text_attr_name="clean_text",
        short_max=500,
        med_max=2000,
        use_metadata=False,
    ):
        self.use_metadata = use_metadata

        def get_bin(record):
            # 1. Prioritize pre-calculated length
            c_len = getattr(record, "clean_length", None)

            # 2. Fallback to manual calculation if DB column is empty
            if c_len is None or c_len == 0:
                raw_val = getattr(record, text_attr_name, None)
                c_len = len(str(raw_val)) if raw_val else 0

            # 3. Categorize into standard bins
            if c_len <= short_max: return "short"
            if c_len <= med_max: return "medium"
            return "long"

        def bucketize(records, is_hazard):
            buckets = {"short": [], "medium": [], "long": []}
            label = 1.0 if is_hazard else 0.0
            for r in records:
                buckets[get_bin(r)].append((r, label))
            return buckets

        # --- 1. Bucketize with Class Tagging ---
        haz_buckets = bucketize(haz_records, True)
        safe_buckets = bucketize(safe_records, False)

        # --- 2. Balanced Sampling per Length Bin ---
        final_pairs = []
        for bucket in ["short", "medium", "long"]:
            h_list = haz_buckets[bucket]
            s_list = safe_buckets[bucket]

            min_count = min(len(h_list), len(s_list))

            if min_count > 0:
                random.shuffle(h_list)
                random.shuffle(s_list)
                # Truncate majority class to match minority class
                final_pairs.extend(h_list[:min_count])
                final_pairs.extend(s_list[:min_count])

            print(f"[Bucket: {bucket}] Balanced to {min_count * 2} samples")

        # Global shuffle to eliminate chronological/bucket biases
        random.shuffle(final_pairs)

        # --- 3. Build Feature Matrix ---
        features = []
        labels = []

        for record, label in final_pairs:
            emb = getattr(record, attr_name, None)
            if emb is None:
                continue

            # Base Embedding (e.g., 384-dim or 768-dim)
            emb = np.asarray(emb, dtype=np.float32)

            # --- HYBRID INJECTION LOGIC ---
            if use_metadata:
                meta = getattr(record, "metadata_vector", None)
                if meta is None:
                    continue
                # Append exact heuristic flags (e.g., 8-dim)
                meta = np.asarray(meta, dtype=np.float32)
                emb = np.concatenate([emb, meta], axis=0)

            features.append(emb)
            labels.append(label)

        if not features:
            raise ValueError("CRITICAL: No valid samples found after filtering.")

        # Stack into contiguous memory blocks for XGBoost DMatrix speed
        self.X = np.stack(features).astype(np.float32)
        self.y = np.asarray(labels, dtype=np.float32)


# ======================================================================
# TRAINING & EXPORT SEQUENCE
# ======================================================================

async def train_and_export(
    mode="text",
    label_col="label",
    haz_val="spam",
    safe_val="ham",
    attr_name="text_embedding",
    use_metadata=False,
):
    print(f"\n--- [INITIATING] {mode.upper()} XGB Training Sequence ---")

    if not Tortoise._inited:
        await Tortoise.init(config=TORTOISE_ORM)

    # --- 1. Dynamic Model Selection ---
    ModelClass = OpenDataSet if mode == "text" else PhishingURL

    if mode == "text":
        s_max, m_max = 200, 1000
        text_attr = "clean_text"
        base_dim = settings.DIM_TEXT
    else:
        s_max, m_max = 50, 150
        text_attr = "original_url"
        base_dim = settings.DIM_URL

    meta_dim = 8 if (mode == "url" and use_metadata) else 0
    input_dim = base_dim + meta_dim

    # --- 2. Data Fetching ---
    haz = await ModelClass.filter(**{f"{attr_name}__isnull": False, label_col: haz_val}).all()
    safe = await ModelClass.filter(**{f"{attr_name}__isnull": False, label_col: safe_val}).all()

    print(f"Hazard samples: {len(haz)}")
    print(f"Safe samples:   {len(safe)}")

    if not haz or not safe:
        print("CRITICAL: Insufficient data for stratification.")
        return

    # --- 3. Dataset Preparation ---
    dataset = StratifiedDataset(
        haz, safe, attr_name=attr_name, text_attr_name=text_attr,
        short_max=s_max, med_max=m_max, use_metadata=use_metadata,
    )

    X = dataset.X
    y = dataset.y

    # --- 4. Strict Data Isolation (Train / ES / Cal / Test) ---
    # XGB early stopping and Platt calibration CANNOT share data, or the 
    # calibration will overfit to the early-stopping bias.
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, stratify=y, random_state=42)
    
    # Split remaining 30% into 3 equal chunks (10% Early Stop, 10% Calibrate, 10% Final Test)
    X_val_es, X_temp2, y_val_es, y_temp2 = train_test_split(X_temp, y_temp, test_size=0.66, stratify=y_temp, random_state=42)
    X_val_cal, X_test, y_val_cal, y_test = train_test_split(X_temp2, y_temp2, test_size=0.50, stratify=y_temp2, random_state=42)

    print(f"Train (Gradient):   {len(X_train)}")
    print(f"Val (Early Stop):   {len(X_val_es)}")
    print(f"Val (Calibration):  {len(X_val_cal)}")
    print(f"Test (Unseen):      {len(X_test)}")

    # --- 5. Base XGBoost Classifier (Mode-Specific Parameters) ---
    if mode == "url":
        # Targeted for high-density URL patterns
        params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "n_estimators": 1000,
            "max_depth": 8,                # Deeper for URL structural logic
            "learning_rate": 0.03,         # Faster convergence for dense data
            "subsample": 0.8,              # Use more data per tree
            "colsample_bytree": 0.8,       # See more embedding dims
            "reg_lambda": 3.0,             # Softer penalty
            "min_child_weight": 5,         # Catch smaller malicious patterns
            "tree_method": "hist",
            "random_state": 42,
            "n_jobs": 4,
        }
        es_rounds = 30
    else:
        # Targeted for generalization in sparse Text embeddings
        params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "n_estimators": 1000,
            "max_depth": 4,                # Shallower to prevent memorization
            "learning_rate": 0.01,         # Slow, deliberate learning
            "subsample": 0.7,
            "colsample_bytree": 0.5,
            "reg_lambda": 10.0,            # Heavy L2 penalty
            "min_child_weight": 15,        # Require broad patterns
            "tree_method": "hist",
            "random_state": 42,
            "n_jobs": 4,
        }
        es_rounds = 25

    # Use this for the actual training with Early Stopping
    base_model = XGBClassifier(**params, early_stopping_rounds=es_rounds)

    print(f"--- Training Base Model with Early Stopping ---")
    base_model.fit(
        X_train, y_train,
        eval_set=[(X_val_es, y_val_es)],
        verbose=200
    )

    # --- 6. Platt Scaling (Probability Calibration) ---
    cal_method = "sigmoid" if mode == "text" else "isotonic"
    print(f"--- [CALIBRATING] Applying {cal_method.capitalize()} Scaling ---")
    frozen_clf = FrozenEstimator(base_model)
    calibrated_model = CalibratedClassifierCV(
        estimator=frozen_clf,
        method=cal_method, # Prioritize nuance on text, and F1 on url
    )
    # This will now work because cal_base doesn't have early_stopping_rounds set in __init__
    calibrated_model.fit(X_val_cal, y_val_cal)

    # --- 7. Evaluation (Strictly on Unseen Test Set) ---
    probs = calibrated_model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    print("\n--- [FINAL REPORT] PERFORMANCE ON UNSEEN TEST SET ---")
    print(classification_report(y_test, preds, target_names=[str(safe_val), str(haz_val)]))
    
    print("--- CONFUSION MATRIX ---")
    print(confusion_matrix(y_test, preds))
    
    print("--- ROC AUC ---")
    print(f"{roc_auc_score(y_test, probs):.6f}")

    extreme_count = np.sum((probs > 0.99) | (probs < 0.01))
    print("--- RAC CONFIDENCE ANALYSIS ---")
    print(f"Extreme Predictions (>99% or <1%): {extreme_count} ({extreme_count / len(probs):.2%})")
    print(f"Average RAC Calibration Confidence: {np.mean(np.abs(probs - 0.5) + 0.5):.4f}")

    # --- 8. Dual Export (XAI + Pipeline) ---
    export_dir = settings.TEXT_MODEL_PATH if mode == "text" else settings.URL_MODEL_PATH
    export_dir.mkdir(parents=True, exist_ok=True)

    # A. Export Raw Booster for SHAP Explainer (Native JSON)
    base_model.save_model(export_dir / "xgboost_base_xai.json")
    
    # B. Export Calibrated Model for RAC Pipeline Inference (Joblib)
    joblib_path = export_dir / "calibrated_classifier.joblib"
    joblib.dump(calibrated_model, joblib_path)

    print(f"\nSUCCESS: {mode.upper()} Dual-Export Complete.")
    print(f"  -> XAI Model:      xgboost_base_xai.json")
    print(f"  -> Pipeline Model: calibrated_classifier.joblib")


# ======================================================================
# MAIN EXECUTION
# ======================================================================
async def main():
    await train_and_export(
        mode="text", 
        label_col="label", 
        haz_val="spam", 
        safe_val="ham", 
        attr_name="text_embedding"
    )
    
    await train_and_export(
        mode="url", 
        label_col="is_malicious", 
        haz_val=True, 
        safe_val=False, 
        attr_name="url_embedding",
        use_metadata=True
    )

if __name__ == "__main__":
    asyncio.run(main())