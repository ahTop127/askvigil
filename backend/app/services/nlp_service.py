import numpy as np
import asyncio
from urlextract import URLExtract
import re
import httpx
import socket
import ipaddress
from urllib.parse import urlparse

from app.core.registry import MODEL_REGISTRY
from app.services.retrieval_services import hybrid_search_rrf

# Initialize once globally
# extract_email=False: Stops it from hunting for @ symbols
# cache_dns=False: Prevents it from trying to 'verify' if a URL is alive
extractor = URLExtract(extract_email=False, cache_dns=False)
# Don't bother checking for a newer TLD list for a week
extractor.update_when_older = 168  # hours in a week


async def is_internal_ip(hostname: str) -> bool:
    """Non-blocking check for internal IP addresses."""
    if not hostname:
        return False  # Treat empty as unsafe
    try:
        # Offload the blocking DNS call to a separate thread
        ip_addr = await asyncio.to_thread(socket.gethostbyname, hostname)
        ip_obj = ipaddress.ip_address(ip_addr)
        # Check against private, loopback, and link-local (metadata) ranges
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
    except Exception:
        # If we can't resolve it at all, it's safer to treat as suspicious
        # or let the request fail naturally.
        return True


async def safe_resolve_redirect(url: str) -> tuple[str, bool]:
    hostname = urlparse(url).hostname
    if not hostname or await is_internal_ip(hostname):
        return url, False

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Vigil/1.0"}

    # We define the hook INSIDE so it has access to the logic
    async def on_request(request):
        host = urlparse(str(request.url)).hostname
        if await is_internal_ip(host):
            # Raising an error here stops the redirect chain immediately
            raise httpx.ConnectError(f"SSRF Blocked: {host}")

    try:
        # Note: We use AsyncClient and 'mount' the hook
        async with httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            max_redirects=5,
            timeout=httpx.Timeout(5.0),
        ) as client:
            # This ensures every redirect is checked BEFORE the request is sent
            client.event_hooks["request"] = [on_request]

            response = await client.head(url)
            return str(response.url), True

    except Exception as e:
        # This catches our SSRF error, timeouts, and dead links
        print(f"[SafeResolve] Security block or resolution error: {str(e)}")
        return url, False


def mean_pooling(model_output, attention_mask):
    """Pooling for MiniLM: Average of token embeddings."""
    token_embeddings = model_output[0]
    input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
    return np.sum(token_embeddings * input_mask_expanded, 1) / np.clip(
        input_mask_expanded.sum(1), a_min=1e-9, a_max=None
    )


async def get_onnx_embedding(input_data: str | list[str], mode: str = "text"):
    config = MODEL_REGISTRY[mode]
    tokenizer = config["tokenizer"]
    session = config["session"]

    # Normalize input to a list
    is_single = isinstance(input_data, str)
    texts = [input_data] if is_single else input_data

    batch_embeddings = []

    for text in texts:
        # 1. Sandwich Truncation
        if len(text) > 4000:
            text = text[:2000] + " " + text[-2000:]

        # 2. Tokenize with Stride (The Rolling Window)
        encoded = tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            stride=256,
            return_overflowing_tokens=True,
            return_tensors="np",
        )

        # 3. Process windows for this specific text
        window_embs = []
        # 'input_ids' will have shape [num_windows, seq_len]
        for i in range(len(encoded["input_ids"])):
            inputs = {
                "input_ids": encoded["input_ids"][i : i + 1].astype(np.int64),
                "attention_mask": encoded["attention_mask"][i : i + 1].astype(np.int64),
            }
            if "token_type_ids" in encoded:
                inputs["token_type_ids"] = encoded["token_type_ids"][i : i + 1].astype(
                    np.int64
                )

            outputs = await asyncio.to_thread(session.run, None, inputs)

            if mode == "text":
                # Mean_pooling function expects (model_output, attention_mask)
                emb = mean_pooling(outputs, encoded["attention_mask"][i : i + 1])
            else:
                emb = outputs[0][:, 0, :]  # URLBERT CLS
            window_embs.append(emb)

        # 4. Global Max Pooling for this text
        # Collapses [num_windows, 1, dim] -> [dim]
        combined = np.max(np.stack(window_embs), axis=0).flatten()

        # 5. L2 Normalization (Standard for Cosine Similarity)
        norm = np.linalg.norm(combined)
        combined = combined / (norm + 1e-9)  # Avoid division by zero

        batch_embeddings.append(combined.astype(np.float32))

    final_result = np.array(batch_embeddings)
    return final_result[0] if is_single else final_result


async def scan_url(raw_url: str):
    # 1. Safely resolve redirects, because phishers hide behind shorteners.
    resolved_url, resolved_successfully = await safe_resolve_redirect(raw_url)

    # 2. Decision Branch (URL MLP Classifier)
    vector = await get_onnx_embedding(resolved_url, mode="url")

    session = MODEL_REGISTRY["url_classifier"]["session"]
    output = await asyncio.to_thread(
        session.run, None, {"input": vector.reshape(1, -1)}
    )
    risk_score = float(output[0][0][0])  # Softmax [Hazard, Safe]

    # 3. Evidence Branch (Historical Discovery)
    # We search using the RESOLVED vector to find similar malicious structures
    # We use source='url_dataset' to prevent searching text rows
    top_matches = await hybrid_search_rrf(
        resolved_url, vector, source="url", limit=5, k=20
    )

    return {
        "risk_score": round(risk_score, 4),
        "resolved_url": resolved_url,
        "resolved_successfully": resolved_successfully,  # Flag raised here
        "decision": "flagged"
        if risk_score > 0.8
        else "clear",  # Higher threshold for URLs
        "evidence": {"match_count": len(top_matches), "top_matches": top_matches},
    }


async def scan_text(text: str):
    # 1. Decision Branch (MLP)
    vector = await get_onnx_embedding(text, mode="text")

    # Run ONNX inference on raw 384-dim vector
    session = MODEL_REGISTRY["text_classifier"]["session"]
    # We use asyncio.to_thread to keep the event loop non-blocking
    output = await asyncio.to_thread(
        session.run, None, {"input": vector.reshape(1, -1)}
    )
    risk_score = float(output[0][0][0])

    # 2. Evidence Branch (HNSW + BM25)
    # k=20 handles the RRF decay curve standardly without manual squaring
    top_matches = await hybrid_search_rrf(text, vector, "text", limit=5, k=20)

    # 3. Merged Response
    return {
        "risk_score": round(risk_score, 4),
        "decision": "flagged" if risk_score > 0.75 else "clear",
        "evidence": {"match_count": len(top_matches), "top_matches": top_matches},
    }


async def scan_unified_text(raw_text: str):
    """
    The Parallel Execution Pipeline:
    1. Standardizes text (Masking URLs and Numbers).
    2. Runs Text Classifier (MLP on 384-dim).
    3. Runs URL Scanner (URLBert).
    4. Performs Search (RRF for evidence).
    """
    # 1. Parity Parsing
    clean_text, urls = standardize_text(raw_text)

    results = {"text_analysis": None, "url_analysis": [], "overall_risk_score": 0.0}

    # 2. Text Decision (Independent Branch)
    if clean_text:
        # scan_text now only takes the 384-dim embedding
        results["text_analysis"] = await scan_text(clean_text)  # MiniLM
        results["overall_risk_score"] = results["text_analysis"]["risk_score"]

    # 3. URL Decision (Independent Branch)
    for url in urls:
        url_res = await scan_url(url)  # URLBert
        results["url_data"].append(url_res)

        # Simple Max-pooling: If a URL is high risk, it bumps the overall score
        results["overall_risk_score"] = max(
            results["overall_risk_score"], url_res["risk_score"]
        )

    return results


def standardize_text(text: str, label: str = None) -> str:
    """
    Unified Parser: Extracts URLs, masks digits, and returns parity-ready data.
    Used for: Data Wrangling, Training, and Inference.
    """
    if not isinstance(text, str) or not text.strip():
        return "", []

    # 1. Fix garbled characters and special punctuation marks
    repls = {"’": "'", "–": "-", "“": '"', "”": '"', "—": "-", " ": " "}
    for old, new in repls.items():
        text = text.replace(old, new)

    # 2. Extract URLs using parity library (urlextract)
    # Done BEFORE number replacement to avoid mangling IP addresses or ports
    urls = extractor.find_urls(text)

    # 3. Mask URLs with URL token ([URL] gets split to 3 tokens, URL is 1)
    # We sort by length descending to avoid partial replacement (e.g., bit.ly/123 vs bit.ly)
    for u in sorted(urls, key=len, reverse=True):
        text = text.replace(u, " URL ")

    # 4. Clean up HTML residues and extra spaces
    text = re.sub(r"&[a-z0-9#]+;", " ", text)

    # 5. Label driven legacy placeholders replacement
    # If it's spam, we assume it's a 'Big Number' (000). If ham, a 'Small Number' (0).
    placeholder = " 000 " if label == "spam" else " 0 "
    text = re.sub(r"(?i)escape(number|long|url)", placeholder, text)

    # 6. Standard Numeric Masking (Shape-Preserving for modern text)
    # This maintains parity between legacy placeholders and real numbers.'
    text = re.sub(r"\d{3,}", " 000 ", text)
    text = re.sub(r"\d{1,2}", " 0 ", text)

    # 7. Formatting
    text = re.sub(r"\s+", " ", text).strip()

    return text, urls
