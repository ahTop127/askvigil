import numpy as np
import asyncio
import torch
from urlextract import URLExtract
from app.core.lifespan import MODEL_REGISTRY
from app.services.retrieval_services import hybrid_search_rrf

extractor = URLExtract()


async def safe_resolve_redirect(url: str) -> str:
    """
    TODO [Future Work]: Implement Redirect Resolver.
    Must safely expand shortlinks (bit.ly, t.co) without executing malicious payloads.
    Consider using `httpx` with `follow_redirects=True` and strict timeouts,
    or a dedicated secure link preview microservice.
    """
    return url


def mean_pooling(model_output, attention_mask):
    """Pooling for MiniLM: Average of token embeddings."""
    token_embeddings = model_output[0]
    input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
    return np.sum(token_embeddings * input_mask_expanded, 1) / np.clip(
        input_mask_expanded.sum(1), a_min=1e-9, a_max=None
    )


async def get_onnx_embedding(input_data: str | list[str], mode: str = "text"):
    """
    Unified inference call. Supports single strings or lists (batches).
    """
    config = MODEL_REGISTRY[mode]
    tokenizer = config["tokenizer"]
    session = config["session"]

    # Tokenize (Handles both str and list[str] natively)
    encoded_input = tokenizer(
        input_data, padding=True, truncation=True, max_length=512, return_tensors="np"
    )

    # Run Inference
    # input_feed maps tokenizer outputs to ONNX expected inputs (input_ids, attention_mask, etc.)
    inputs = {k: v for k, v in encoded_input.items()}
    # Run Inference on the threadpool to keep FastAPI responsive
    outputs = await asyncio.to_thread(session.run, None, inputs) # outputs[0] = last_hidden_state, outputs[1] = attentions (if exported)

    if mode == "text":
        # Returns [Batch, 384]
        embeddings = mean_pooling(outputs, encoded_input["attention_mask"])
    else:
        # URLBert [Batch, 768] - Grab the CLS token for every item in batch
        embeddings = outputs[0][:, 0, :]

    # If it's a single string, we return it as a flat array [384]
    # If it's a list, we return the matrix [N, 384]
    return embeddings.squeeze() if isinstance(input_data, str) else embeddings


async def scan_url(raw_url: str):
    """Processes a single URL through resolution and embedding."""
    resolved_url = await safe_resolve_redirect(raw_url)

    # URLBERT Inference
    obj = MODEL_REGISTRY.get("url")
    if not obj:
        return {"error": "URL model not loaded"}

    inputs = obj["tokenizer"](
        resolved_url, return_tensors="pt", truncation=True, max_length=512
    )

    # Using torch-cpu, no_grad is critical for performance
    with torch.no_grad():
        # Offload CPU-bound inference to threadpool to prevent blocking the event loop
        outputs = await asyncio.to_thread(lambda: obj["model"](**inputs))

    cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()

    # TODO: Pass cls_embedding to the Risk Head / Database similarity search
    return {
        "original_url": raw_url,
        "resolved_url": resolved_url,
        # "embedding_sample": cls_embedding[:5].tolist(),
        "embedding": cls_embedding.tolist(),
        "risk_score": 0.0,
    }


async def scan_text(text: str):
    # 1. Get Embedding (ONNX INT8)
    emb_data = await get_onnx_embedding(text, mode="text")
    vector = emb_data.tolist()

    # 2. Hybrid Retrieval (RRF)
    # This fetches the "Institutional Memory"
    top_matches = await hybrid_search_rrf(text, vector, limit=5)

    # 3. Preparation for MLP Training
    # We extract the RRF scores of the top 5 matches to feed into the MLP
    rrf_features = [m['rrf_score'] for m in top_matches]
    
    # Pad if fewer than 5 matches found
    while len(rrf_features) < 5:
        rrf_features.append(0.0)

    return {
        "embedding": vector,
        "rrf_features": rrf_features, # These go to the MLP in Step 5
        "top_matches": top_matches
    }


async def scan_unified_text(raw_text: str):
    """Extracts URLs, cleans text, and runs both through respective models."""
    urls = extractor.find_urls(raw_text)

    clean_text = raw_text
    for u in urls:
        clean_text = clean_text.replace(u, "[URL]")

    results = {"text_data": None, "url_data": []}

    if clean_text.strip():
        results["text_data"] = await scan_text(clean_text)

    for url in urls:
        results["url_data"].append(await scan_url(url))

    return results
