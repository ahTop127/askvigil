import numpy as np


def compute_loo_deltas(
    unpooled_tokens: np.ndarray, xgb_model, meta_vector: np.ndarray = None
) -> np.ndarray:
    """Computes Leave-One-Out ablation in a single batch pass (Sklearn-compatible)."""
    N, D = unpooled_tokens.shape
    if N <= 1:
        return np.zeros(N, dtype=np.float32)

    # 1. Base Mean and Ablation
    total_sum = np.sum(unpooled_tokens, axis=0)
    base_mean = total_sum / N
    ablated_means = (total_sum - unpooled_tokens) / (N - 1)

    # 2. Combine into one batch matrix (NumPy Array)
    combined_matrix = np.vstack([base_mean, ablated_means])  # Shape: (N+1, D)

    # 3. Inject Metadata (Crucial for URL Pipeline)
    if meta_vector is not None:
        # Repeat the 8-dim metadata N+1 times to match the batch size
        meta_repeated = np.tile(meta_vector, (N + 1, 1))
        # Concatenate it to the right of the embeddings (Total Dim: D + 8)
        combined_matrix = np.hstack([combined_matrix, meta_repeated])

    # 4. Batch Inference (SKLEARN API)
    # We pass the raw NumPy array, NOT a DMatrix.
    # predict_proba returns shape (N+1, 2) where column index 1 is usually the "Hazard/Scam" class.
    all_preds_proba = xgb_model.predict_proba(combined_matrix)

    # Extract the probability of the hazard class for all N+1 scenarios
    hazard_probs = all_preds_proba[:, 1]

    # 5. Delta = Base Score - Ablated Score
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
) -> list:
    """Zips the ML tensors into a JSON-friendly array. Lexical match is calculated in-memory."""
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

        # THE FIX 2: Strip whitespace for accurate length checking
        clean_token = token_text.strip()

        # --- IN-MEMORY LEXICAL CHECK ---
        # We only flag words longer than 3 characters to prevent the UI from
        # highlighting every "a", "to", "the", or random slash "/" in a URL.
        is_lexical = False
        if len(clean_token) > 3:
            is_lexical = clean_token.lower() in doc_text_lower

        explanation_array.append(
            {
                "token_text": token_text,
                "start_char": start_char,
                "end_char": end_char,
                "xgb_predictive_delta": round(float(xgb_deltas[idx]), 4),
                "semantic_similarity": round(float(semantic_scores[idx]), 4),
                "is_lexical_match": is_lexical,
            }
        )
    return explanation_array
