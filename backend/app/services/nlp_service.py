import numpy as np
import asyncio
import torch
from urlextract import URLExtract
from app.core.lifespan import MODEL_REGISTRY

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
    return np.sum(token_embeddings * input_mask_expanded, 1) / np.clip(input_mask_expanded.sum(1), a_min=1e-9, a_max=None)

async def get_onnx_embedding(text: str, mode: str = "text"):
    config = MODEL_REGISTRY[mode]
    tokenizer = config["tokenizer"]
    session = config["session"]

    # Tokenize
    encoded_input = tokenizer(text, padding=True, truncation=True, max_length=512, return_tensors='np')
    
    # Run Inference
    # input_feed maps tokenizer outputs to ONNX expected inputs (input_ids, attention_mask, etc.)
    inputs = {k: v for k, v in encoded_input.items()}
    outputs = session.run(None, inputs) # outputs[0] = last_hidden_state, outputs[1] = attentions (if exported)
    
    if mode == "text":
        # MiniLM typically uses Mean Pooling
        return mean_pooling(outputs, encoded_input['attention_mask']).flatten()
    else:
        # URLBert uses CLS Pooling ([CLS] is index 0)
        return outputs[0][:, 0, :].flatten()

async def scan_url(raw_url: str):
    """Processes a single URL through resolution and embedding."""
    resolved_url = await safe_resolve_redirect(raw_url)

    # URLBERT Inference
    obj = MODEL_REGISTRY.get("url_bert")
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
    """Dedicated function for MiniLM inference and text risk scoring."""
    obj = MODEL_REGISTRY.get("text_minilm")
    if not obj:
        return {"error": "Text model not loaded"}

    # Offload CPU-bound inference to threadpool
    emb = await asyncio.to_thread(obj["model"].encode, text)

    return {
        "clean_text": text,
        # "embedding_sample": emb[:5].tolist(),
        "embedding": emb.tolist(),
        "category": "Pending",
        "risk_score": 0.0,
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
