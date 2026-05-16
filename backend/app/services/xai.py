import numpy as np


def compute_loo_deltas(
    unpooled_tokens: np.ndarray, xgb_model, meta_vector: np.ndarray = None
) -> np.ndarray:
    """
    Computes Leave-One-Out ablation in a single batch pass (Sklearn-compatible).
    """
    N, D = unpooled_tokens.shape
    if N <= 1:
        return np.zeros(N, dtype=np.float32)

    # 1. Base Mean and Ablation
    total_sum = np.sum(unpooled_tokens, axis=0)
    base_mean = total_sum / N

    # 2. Pre-allocate single matrix block to eliminate O(N^2) memory copying overhead
    M = len(meta_vector) if meta_vector is not None else 0
    # Single allocation block in memory
    combined_matrix = np.empty((N + 1, D + M), dtype=np.float32)

    # 3. Fill matrix in-place using zero-copy slicing and broadcasting
    combined_matrix[0, :D] = base_mean
    # Broadcast subtraction: (1, D) - (N, D) -> fits perfectly into rows 1 to N+1
    combined_matrix[1:, :D] = (total_sum - unpooled_tokens) / (N - 1)

    # 4. Fill the metadata in-place (Exploit NumPy broadcasting, no np.tile needed)
    if meta_vector is not None:
        combined_matrix[:, D:] = meta_vector

    # 5. Batch Inference (XGBoost SKLEARN API)
    # We pass the raw NumPy array, NOT a DMatrix.
    # predict_proba returns shape (N+1, 2) where column index 1 is usually the "Hazard/Scam" class.
    all_preds_proba = xgb_model.predict_proba(combined_matrix)

    # 5. Extract hazard probabilities and compute Leave-One-Out deltas
    # Note: Slicing creates a memory 'view', keeping this step O(1) in space overhead
    hazard_probs = all_preds_proba[:, 1]
    # Delta = Base Score - Ablated Score
    # Positive delta means the token pushes the score UP (malicious)
    return hazard_probs[0] - hazard_probs[1:]


def generate_text_explanation(
    raw_text: str,
    offset_mapping: np.ndarray,
    input_ids: np.ndarray,
    unpooled_tokens: np.ndarray,
    doc_embedding: np.ndarray,
    doc_text: str,
    xgb_deltas: np.ndarray,
    mode: str = "text",
) -> list:
    """
    Zips the ML tensors into a JSON-friendly array.
    Lexical match is calculated in-memory.
    """
    # Define normalization constants
    # norm_scale: the XGB delta that equals 100% heat (e.g., 0.10 = 10% shift)
    # sem_bounds: (floor, divisor) to map similarity to 0.0 - 1.0
    config = {
        "text": {"norm_scale": 0.10, "sem_bounds": (0.3, 0.4)},  # 0.3->0.7 range
        "url": {"norm_scale": 0.15, "sem_bounds": (0.2, 0.5)},  # 0.2->0.7 range
    }.get(mode, "text")

    explanation_array = []
    # ---------------------------------------------------------
    # Normalization and mean-Centering to break the Anisotropy Cone
    # ---------------------------------------------------------
    # 1. Calculate the center of the cone
    token_mean = np.mean(unpooled_tokens, axis=0, keepdims=True)

    # 2. Shift all vectors to the new origin
    centered_tokens = unpooled_tokens - token_mean
    centered_doc = doc_embedding - np.squeeze(token_mean)

    # 3. L2 Normalize the centered vectors
    norms_unpooled = np.linalg.norm(centered_tokens, axis=1, keepdims=True)
    unpooled_normalized = centered_tokens / (norms_unpooled + 1e-9)

    norm_doc = np.linalg.norm(centered_doc)
    doc_normalized = centered_doc / (norm_doc + 1e-9)

    # 4. Cosine Similarity (Scores will now have deep variance!)
    semantic_scores = np.dot(unpooled_normalized, doc_normalized)
    # ---------------------------------------------------------

    # Lowercase for case-insensitive string matching
    doc_text_lower = doc_text.lower() if doc_text else ""

    # Track spans to prevent UI crashes
    seen_spans = set()

    for idx, offset in enumerate(offset_mapping):
        start_char, end_char = int(offset[0]), int(offset[1])
        if start_char == 0 and end_char == 0:
            continue

        # Deduplicate identical character spans
        span_tuple = (start_char, end_char)
        if span_tuple in seen_spans:
            continue
        seen_spans.add(span_tuple)

        token_text = raw_text[start_char:end_char]

        # Strip whitespace for accurate length checking
        clean_token = token_text.strip()

        # --- IN-MEMORY LEXICAL CHECK ---
        # We only flag words longer than 3 characters to prevent the UI from
        # highlighting every "a", "to", "the", or random slash "/" in a URL.
        is_lexical = False
        if len(clean_token) > 3:
            is_lexical = clean_token.lower() in doc_text_lower

        # --- CALCULATE NORMALIZED UI SIGNALS ---
        raw_xgb = float(xgb_deltas[idx])
        raw_sem = float(semantic_scores[idx])

        # Map delta norm scale to 1.0 intensity (Calibrated for Platt Scaling)
        norm_xgb = min(abs(raw_xgb) / config["norm_scale"], 1.0)

        # Map semantic similarity (e.g., 0.3 to 0.7) to a 0.0 to 1.0 scale
        floor, divisor = config["sem_bounds"]
        norm_sem = max(0.0, min((raw_sem - floor) / divisor, 1.0))

        explanation_array.append(
            {
                "token_text": token_text,
                "start_char": start_char,
                "end_char": end_char,
                "xgb_predictive_delta": round(float(xgb_deltas[idx]), 4),
                "semantic_similarity": round(float(semantic_scores[idx]), 4),
                "is_lexical_match": is_lexical,
                # Simplified signals for the Frontend
                "ui_signals": {
                    "norm_xgb": round(norm_xgb, 4),
                    "norm_semantic": round(norm_sem, 4),
                    "is_lexical": is_lexical,
                },
            }
        )
    return explanation_array
