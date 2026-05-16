import numpy as np
import asyncio
from urlextract import URLExtract
import re
import httpx
import socket
import ipaddress
from urllib.parse import urlparse
from typing import List
import math
from collections import Counter
import orjson

from app.core.registry import MODEL_REGISTRY
from app.services.retrieval_services import hybrid_search_rrf
from app.services.xai import compute_loo_deltas, generate_text_explanation

import logging
logger = logging.getLogger(__name__)
###########################################################################
# Parameters

# Threshold (Anything below we will treat as uncertain)
UNKNOWN_THRESHOLD = 0.50
# How far is it from the next type so we can have confidence
MIN_MARGIN = 0.08
MIN_RULE_REQUIRED_THRESHOLD = 0.60

# Extra points for strong keywords
RULE_BOOST = 0.12
STRONG_RULE_BOOST = 0.20

###########################################################################
# Scam prototypes vector
SCAM_TYPES = {
    "Phishing": [
        "A fake bank or financial service message saying the account is blocked, suspended, locked, frozen, or restricted.",
        "A phishing message pretending to be Maybank, CIMB, RHB, Public Bank, Touch n Go, TNG, or another financial service.",
        "A message asking the user to click a link, login, verify, update, or reactivate an account.",
        "A fake security alert about suspicious login, unusual activity, unauthorized transaction, or account verification.",
        "A message using account fear and urgency to make the user reveal banking or login details.",
    ],
    "Job Scam": [
        "A fake part-time job offer promising high salary, easy money, daily pay, commission, or work from home income.",
        "A recruitment scam targeting students with unrealistic pay such as RM10000 per hour or RM500 per day.",
        "A message offering online tasks, likes, reviews, ratings, shopping orders, or product reviews for money.",
        "A job scam asking the user to contact WhatsApp or Telegram to join a task group or recruitment group.",
        "A suspicious job offer that asks for registration fees, deposits, personal details, or bank details.",
    ],
    "OTP Scam": [
        "A message asking the user to share an OTP, TAC, verification code, login code, one-time password, or security code.",
        "A scammer asking the user to forward, send, or reveal a code received by SMS or banking app.",
        "A message pretending to verify identity by requesting a security code or authentication code.",
        "A scam trying to take over the user's banking, e-wallet, social media, or online account using a verification code.",
        "A message saying the user must provide a code to complete verification, payment, login, or account recovery.",
    ],
}

# Regex patterns for each type of scam
KEYWORD_RULES = {
    "Phishing": [
        # Bank / Finance brands
        r"\bmaybank\b",
        r"\bcimb\b",
        r"\brhb\b",
        r"\bpublic bank\b",
        r"\bhong leong\b",
        r"\bambank\b",
        r"\bbank islam\b",
        r"\btng\b",
        r"\btouch n go\b",
        r"\btouch 'n go\b",
        r"\bboost\b",
        r"\bgrabpay\b",
        r"\bduitnow\b",
        r"\bbank\b",
        # Account Threat
        r"account.*blocked",
        r"account.*suspended",
        r"account.*locked",
        r"account.*frozen",
        r"account.*restricted",
        r"card.*blocked",
        r"card.*suspended",
        r"unauthorized.*transaction",
        r"suspicious.*login",
        r"unusual.*activity",
        r"security.*alert",
        # action request
        r"verify.*account",
        r"account.*verification",
        r"reactivate.*account",
        r"update.*account",
        r"login.*account",
        r"click.*verify",
        r"click.*login",
        r"confirm.*details",
        r"verify.*details",
    ],
    "Job Scam": [
        r"part[\s-]?time",
        r"work from home",
        r"\bjob\b",
        r"\bhiring\b",
        r"\brecruit(?:ing|ment)?\b",
        r"\bvacancy\b",
        r"\bposition\b",
        # Student-targeted job scams
        r"university students?",
        r"college students?",
        r"students?\s+wanted",
        r"hiring.*students?",
        r"students?.*hiring",
        # Money / Salary patterns
        r"\bsalary\b",
        r"\bcommission\b",
        r"\bincome\b",
        r"\bearn\b",
        r"earn.*rm",
        r"rm\s*\d+",
        r"rm\s*\d+.*(?:hour|day|daily|week|month)",
        r"rm\s*\d+.*per\s*(?:hour|day|week|month)",
        r"per\s*(?:hour|day|week|month)",
        r"daily.*pay",
        r"weekly.*pay",
        r"fast.*money",
        r"easy.*money",
        r"quick.*cash",
        r"instant.*income",
        r"earn.*(quick|fast|easy)",
        # Common job scam wording
        r"daily.*income",
        r"online task",
        r"\btask\b",
        r"simple.*task",
        r"easy.*money",
        r"high.*pay",
        r"no experience",
        r"flexible.*time",
        r"like.*video",
        r"review.*product",
        r"rating.*task",
        # Platform-based recruitment
        r"telegram.*job",
        r"whatsapp.*job",
        r"contact.*whatsapp",
        r"pm.*whatsapp",
        r"join.*telegram",
        r"join.*whatsapp",
    ],
    "OTP Scam": [
        r"\botp\b",
        r"\btac\b",
        r"verification code",
        r"one[\s-]?time password",
        r"login code",
        r"security code",
        r"authentication code",
        r"authori[sz]ation code",
        # Asking user to reveal code
        r"send.*code",
        r"share.*code",
        r"forward.*code",
        r"give.*code",
        r"provide.*code",
        r"tell.*code",
        r"send.*otp",
        r"share.*otp",
        r"forward.*otp",
        r"give.*otp",
        r"provide.*otp",
        r"send.*tac",
        r"share.*tac",
    ],
}

SCAM_TYPE_NAMES = None
SCAM_TYPE_VECTORS = None


def clean_text(text):
    """Preprocess the text before detection"""
    text = str(text).lower()

    text = re.sub(r"http\S+|www\.\S+", " URL ", text)  # we replace links with URL
    text = re.sub(r"[^a-zA-Z0-9$%.\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_type_embeddings(model):
    """Build semantic prototypes"""
    type_names = []
    type_vectors = []
    # For each scam type, we will build the prototype
    for scam_type, descriptions in SCAM_TYPES.items():
        description_embeddings = model.encode(
            descriptions,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        prototype = np.mean(description_embeddings, axis=0)  # Average all descriptions
        # Normzalization - text has varying length, so we want to normalize and only compare in the direction wise
        prototype = prototype / np.linalg.norm(prototype)

        type_names.append(scam_type)
        type_vectors.append(prototype)
    # Convert list of vectors to matrix
    type_vectors = np.vstack(type_vectors)

    return type_names, type_vectors


# Initialize once globally
# extract_email=False: Stops it from hunting for @ symbols
# cache_dns=False: Prevents it from trying to 'verify' if a URL is alive
extractor = URLExtract(extract_email=False, cache_dns=False)
# Don't bother checking for a newer TLD list for a week
extractor.update_when_older = 168  # hours in a week


async def build_type_embeddings():
    """Load it first so it wouldn't need to constantly load"""
    type_names = []
    type_vectors = []

    for scam_type, descriptions in SCAM_TYPES.items():
        description_embeddings = await get_onnx_embedding(
            descriptions,
            mode="text",
        )

        prototype = np.mean(description_embeddings, axis=0)
        prototype = prototype / (np.linalg.norm(prototype) + 1e-9)

        type_names.append(scam_type)
        type_vectors.append(prototype)

    type_vectors = np.vstack(type_vectors).astype(np.float32)

    return type_names, type_vectors


async def get_scam_type_prototypes():
    global SCAM_TYPE_NAMES, SCAM_TYPE_VECTORS

    if SCAM_TYPE_NAMES is None or SCAM_TYPE_VECTORS is None:
        SCAM_TYPE_NAMES, SCAM_TYPE_VECTORS = await build_type_embeddings()

    return SCAM_TYPE_NAMES, SCAM_TYPE_VECTORS


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
    """Resolve urls to their final destination safely. Max 5 redirects or 5s."""
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
        logger.info(f"[SafeResolve] Security block or resolution error: {str(e)}")
        return url, False


def mean_pooling(model_output, attention_mask):
    """Pooling for MiniLM: Average of token embeddings."""
    token_embeddings = model_output[0]
    input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
    return np.sum(token_embeddings * input_mask_expanded, 1) / np.clip(
        input_mask_expanded.sum(1), a_min=1e-9, a_max=None
    )


async def get_onnx_embedding(
    input_data: str | list[str], mode: str = "text", return_xai: bool = False
):
    """Generates L2-normalized embeddings using an ONNX runtime session.

    Handles long texts gracefully via 'sandwich truncation' (taking the first and
    last 2000 characters) followed by a sliding window/strided tokenization approach.
    Multiple window embeddings for a single text are aggregated using global max-pooling.

    Args:
        input_data: A single string or a list of strings to embed.
        mode: The model configuration key to use from `MODEL_REGISTRY`
            (e.g., "text" or "url"). Defaults to "text".
        return_xai: If True, returns the unpooled tokens, input IDs, and
            offset mappings for explainable AI analysis. Only supported for single
            string inputs. Defaults to False.

    Returns:
        If return_xai is False:
            A numpy array of embeddings. Shape is (dim,) for a single string or
            (batch_size, dim) for a list of strings.
        If return_xai is True:
            A tuple of (embeddings, xai_dict).

    Raises:
        ValueError: If return_xai is requested for a batch (list) of inputs.
    """
    if return_xai and not isinstance(input_data, str):
        raise ValueError("XAI data extraction is only supported for single string inputs.")
    
    config = MODEL_REGISTRY[mode]
    tokenizer = config["tokenizer"]
    session = config["session"]

    # Normalize input to a list
    is_single = isinstance(input_data, str)
    texts = [input_data] if is_single else input_data
    batch_embeddings = []
    # XAI variables (only populated if return_xai is True and is_single is True)
    xai_dict = {}

    for text in texts:
        # 1. Sandwich Truncation
        if len(text) > 4000:
            text = text[:2000] + " " + text[-2000:]

        # 2. Tokenize with Stride (The Rolling Window)
        # If XAI is requested, we disable stride/rolling window
        # so we get a perfect 1:1 character mapping.
        stride_val = 0 if return_xai else 256
        encoded = tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            stride=stride_val,
            return_overflowing_tokens=True,
            return_offsets_mapping=return_xai,  # Required for XAI
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

            # --- XAI EXTRACTION (Only grab the first window) ---
            if return_xai and i == 0:
                # feature-extraction returns last_hidden_state as outputs[0]
                xai_dict["unpooled_tokens"] = outputs[0][
                    0
                ]  # Shape: (Seq_Len, 384 or 768)
                xai_dict["input_ids"] = encoded["input_ids"][0]
                xai_dict["offset_mapping"] = encoded["offset_mapping"][0]

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
    final_result = final_result[0] if is_single else final_result
    if return_xai:
        return final_result, xai_dict
    return final_result

def explain_text_risk(text: str):
    """Explainable Boosting: Simple keyword-based heuristic to explain why a text might be risky."""
    text_lower = text.lower()
    patterns = [
        {
            "category": "Urgency / pressure",
            "terms": [
                "urgent",
                "immediately",
                "now",
                "limited time",
                "act fast",
                "final warning",
                "register now",
                "verify now",
                "today only",
                "within 24 hours",
                "last chance",
            ],
            "boost": 0.10,
            "severity": "medium",
            "risk_floor": 0.0,
            "reason_template": "This message uses words such as {terms}, which create time pressure or push the user to act quickly.",
        },
        {
            "category": "Suspicious action request",
            "terms": [
                "click here",
                "open this link",
                "using this link",
                "scan qr",
                "download app",
                "verify",
                "login here",
                "register using",
                "confirm your details",
                "update your details",
                "reactivate",
                "claim now",
            ],
            "boost": 0.15,
            "severity": "medium",
            "risk_floor": 0.0,
            "reason_template": "This message uses phrases such as {terms}, which ask the user to take an action such as verifying, clicking, scanning, downloading, registering, or claiming.",
        },
        {
            "category": "Money / reward / job offer",
            "terms": [
                "won",
                "winner",
                "prize",
                "claim",
                "reward",
                "free gift",
                "part time job",
                "work from home",
                "earn",
                "salary",
                "commission",
                "rm",
                "cash",
                "bonus",
                "daily pay",
                "easy money",
                "high pay",
                "guaranteed profit",
            ],
            "boost": 0.20,
            "severity": "high",
            "risk_floor": 0.55,
            "reason_template": "This message uses words such as {terms}, which mention money, rewards, or job offers that are commonly used in scam messages.",
        },
        {
            "category": "Account threat",
            "terms": [
                "account blocked",
                "account suspended",
                "blocked",
                "suspended",
                "security alert",
                "unauthorized transaction",
                "account locked",
                "account frozen",
                "unusual activity",
                "suspicious login",
                "deactivated",
                "restricted",
            ],
            "boost": 0.25,
            "severity": "high",
            "risk_floor": 0.65,
            "reason_template": "This message uses words such as {terms}, which create fear about account access or security.",
        },
        {
            "category": "Sensitive information request",
            "terms": [
                "otp",
                "password",
                "pin",
                "ic number",
                "bank details",
                "login details",
                "card number",
                "tac",
                "verification code",
                "security code",
                "login code",
                "one time password",
                "one-time password",
            ],
            "boost": 0.35,
            "severity": "critical",
            "risk_floor": 0.75,
            "reason_template": "This message uses words such as {terms}, which may indicate a request for sensitive information that should not be shared through chat.",
        },
    ]

    total_boost = 0.0
    highest_risk_floor = 0.0
    explanations = []

    for item in patterns:
        matched_terms = find_terms(text_lower, item["terms"])

        if matched_terms:
            total_boost += item["boost"]
            highest_risk_floor = max(highest_risk_floor, item["risk_floor"])

            explanations.append(
                {
                    "category": item["category"],
                    "matched_terms": matched_terms,
                    "reason": item["reason_template"].format(
                        terms=format_terms(matched_terms)
                    ),
                    "severity": item["severity"],
                    "boost": item["boost"],
                    "risk_floor": item["risk_floor"],
                }
            )

    # combo boost: multiple warning signs together should increase confidence
    categories = [item["category"] for item in explanations]

    if "Account threat" in categories and "Suspicious action request" in categories:
        total_boost += 0.10
        highest_risk_floor = max(highest_risk_floor, 0.75)

    if (
        "Sensitive information request" in categories
        and "Suspicious action request" in categories
    ):
        total_boost += 0.10
        highest_risk_floor = max(highest_risk_floor, 0.80)

    if (
        "Money / reward / job offer" in categories
        and "Urgency / pressure" in categories
    ):
        total_boost += 0.05
        highest_risk_floor = max(highest_risk_floor, 0.65)

    # cap the influence
    total_boost = min(total_boost, 0.75)

    return {
        "total_boost": total_boost,
        "risk_floor": highest_risk_floor,
        "matched_indicators": explanations,
    }


def format_terms(terms: List[str]) -> str:
    """Format the explanations"""
    quoted_terms = [f"'{term}'" for term in terms]

    if len(quoted_terms) == 1:
        return quoted_terms[0]

    if len(quoted_terms) == 2:
        return f"{quoted_terms[0]} and {quoted_terms[1]}"

    return ", ".join(quoted_terms[:-1]) + f", and {quoted_terms[-1]}"


def find_terms(text_lower: str, terms: List[str]) -> List[str]:
    matched = []

    for term in terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, text_lower):
            matched.append(term)

    return matched


def get_rule_boosts(cleaned_text, type_names):
    """Rule boosting for further accuracy"""
    # Create lists and initial values for each type of the scams
    boosts = {scam_type: 0 for scam_type in type_names}
    matched_rules = {scam_type: [] for scam_type in type_names}

    # Now we will go through the scam rules and then see how many it matches
    for scam_type, patterns in KEYWORD_RULES.items():
        # Skip rule which is not in the scam type
        if scam_type not in boosts:
            continue

        match_count = 0
        # Now perform a regex search pattern
        for pattern in patterns:
            if re.search(pattern, cleaned_text):
                match_count += 1
                matched_rules[scam_type].append(pattern)  # keyword

        # If we only match 1, we will add a small boost
        if match_count == 1:
            boosts[scam_type] += RULE_BOOST
        # If it matches more than 2, we add a larger boost
        elif match_count >= 2:
            boosts[scam_type] += STRONG_RULE_BOOST

    return boosts, matched_rules


async def classify_scam_type(text, type_names, type_vectors):
    """Classification of keyword-matched scam type"""
    # Clean the test first
    cleaned = clean_text(text)

    # Convert the input to embeddings
    text_embedding = await get_onnx_embedding(
        cleaned,
        mode="text",
    )

    # Compare the input vector with each type of prototype via dot product
    semantic_scores = np.dot(type_vectors, text_embedding)

    # Get the rule boost
    boosts, matched_rules = get_rule_boosts(cleaned, type_names)

    final_scores = []
    # For each of the scam
    for i, scam_type in enumerate(type_names):
        # Semantic score
        score = float(semantic_scores[i])
        # Rule boost
        score += boosts.get(scam_type, 0.0)
        final_scores.append(score)

    # Converts final score into array
    final_scores = np.array(final_scores)
    # Sort them from the highest score to lowest
    ranked_indices = np.argsort(final_scores)[::-1]

    # Gets the first and second best scores
    best_idx = ranked_indices[0]
    second_idx = ranked_indices[1]

    # Gets their name
    best_type = type_names[best_idx]
    second_type = type_names[second_idx]

    # Convert score into float
    best_score = float(final_scores[best_idx])
    second_score = float(final_scores[second_idx])

    # How confident are we (first compared to second)
    margin = best_score - second_score

    # If the score is below the thereshold, we are unsure
    if best_score < UNKNOWN_THRESHOLD:
        predicted_type = "Not Recognized By Known Type"
        confidence_level = "low"

    elif (
        best_score < MIN_RULE_REQUIRED_THRESHOLD and len(matched_rules[best_type]) == 0
    ):
        predicted_type = "Not Recognized By Known Type"
        confidence_level = "low"

    # If its lower than our margin, its medium confidence
    elif margin < MIN_MARGIN:
        predicted_type = best_type
        confidence_level = "medium"
    # High confidence
    else:
        predicted_type = best_type
        confidence_level = "high"
    return {
        "predicted_type": predicted_type,
        "confidence_level": confidence_level,
    }

 
def get_prevention_guidance(predicted_type: str, decision: str):
    """Providing scam prevention guidance"""
    if decision == "clear":
        return {
            "title": "No immediate scam action needed",
            "summary": "This message does not show strong scam indicators, but still avoid sharing sensitive information in chat.",
            "dont_do": [
                "Do not share passwords, OTP, TAC, IC number, or bank details through chat.",
                "Do not click unfamiliar links without checking the source.",
            ],
            "safer_action": [
                "Verify important requests through official channels.",
            ],
        }

    if predicted_type == "Not Recognized By Known Type":
        return None

    guidance_map = {
        "Phishing": {
            "title": "Before you respond, avoid these actions",
            "summary": "This message may be trying to steal your account or banking details.",
            "dont_do": [
                "Do not click the link in the message.",
                "Do not enter your banking username, password, OTP, TAC, IC number, or card details.",
                "Do not download any app from the message.",
                "Do not reply with personal or financial information.",
                "Do not trust the message only because it mentions a real bank, e-wallet, or delivery company.",
            ],
            "safer_action": [
                "Open the official app or website manually instead of using the message link.",
                "Contact the company using its official hotline or verified support channel.",
                "Delete or ignore the message if the sender cannot be verified.",
            ],
        },
        "OTP Scam": {
            "title": "Before you respond, avoid these actions",
            "summary": "This message may be trying to get your verification code or take over an account.",
            "dont_do": [
                "Do not share your OTP, TAC, verification code, login code, or security code.",
                "Do not forward screenshots of SMS codes or app notifications.",
                "Do not let someone pressure you by saying the code is needed urgently.",
                "Do not approve login or payment requests that you did not start.",
            ],
            "safer_action": [
                "Ignore requests asking for OTP or TAC.",
                "Check your account directly through the official app.",
                "Change your password if you think someone is trying to access your account.",
            ],
        },
        "Job Scam": {
            "title": "Before you respond, avoid these actions",
            "summary": "This message may be a fake job offer using high pay or easy tasks to attract you.",
            "dont_do": [
                "Do not pay registration fees, deposits, training fees, or task unlock fees.",
                "Do not send your IC, bank details, or personal documents to unknown recruiters.",
                "Do not join suspicious Telegram or WhatsApp task groups.",
                "Do not trust offers that promise unusually high pay for simple tasks.",
            ],
            "safer_action": [
                "Check whether the company and recruiter are real.",
                "Search for the job through the company’s official website or verified job platforms.",
                "Ask for a formal job description, company email, and interview process.",
            ],
        },
    }

    return guidance_map.get(predicted_type)


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

    # Define what 'noise' tokens look like
    noise_tokens = {"URL", "0", "000"}
    tokens = [t.lower().strip() for t in clean_text.split()]

    # 2. Count real human words, ignoring punctuation
    human_words = [
        t
        for t in tokens
        if t not in noise_tokens
        and any(
            char.isalnum() for char in t
        )  # Must contain at least one letter or number
    ]

    results = {"text_analysis": None, "url_analysis": [], "overall_risk_score": -1.0}

    # 2. Text Decision (Independent Branch)
    if clean_text and len(human_words) > 5:
        # scan_text now only takes the 384-dim embedding
        results["text_analysis"] = await scan_text(clean_text)  # MiniLM
        results["overall_risk_score"] = results["text_analysis"]["risk_score"]

        # Do NOT return here or urls will never be analyzed
    else:
        # Human word content is <= 5, does not make sense to analyze scam intent here as it is likely just a URL, let urlbert handle it.
        pass

    # 3. URL Decision (Independent Branch)
    for url in urls:
        url_res = await scan_url(url)
        results["url_analysis"].append(url_res)

    # 4. Global Dynamic Fusion (Instead of Max-Pooling)
    fusion_items = []

    if results["text_analysis"]:
        risk = results["text_analysis"]["risk_score"]
        conf = probability_confidence(risk)
        fusion_items.append((risk, conf, 1.0))  # Base weight 1.0

    for u_res in results["url_analysis"]:
        risk = u_res["risk_score"]
        conf = probability_confidence(risk)
        fusion_items.append((risk, conf, 1.0))  # Base weight 1.0

    if fusion_items:
        total_eff = sum(base * conf for _, conf, base in fusion_items)
        if total_eff > 1e-9:
            final_risk = (
                sum(risk * (base * conf) for risk, conf, base in fusion_items)
                / total_eff
            )
        else:
            final_risk = sum(risk * base for risk, conf, base in fusion_items) / sum(
                base for _, _, base in fusion_items
            )

        results["overall_risk_score"] = round(final_risk, 4)

    return results


def standardize_text(text: str, label: str = None) -> str:
    """
    Unified Parser: Extracts URLs, masks digits, and returns parity-ready data.
    Used for: Data Wrangling, Training, and Inference.
    """
    if not isinstance(text, str) or not text.strip():
        return "", []

    # 1. Normalize Protocol (Crucial for URLBert)
    # If the input is just a URL, we fix it first.
    if "." in text and " " not in text:
        text = standardize_url(text)

    # 2. Fix garbled characters and special punctuation marks
    repls = {"’": "'", "–": "-", "“": '"', "”": '"', "—": "-", " ": " "}
    for old, new in repls.items():
        text = text.replace(old, new)

    # 3. Extract URLs using parity library (urlextract)
    # Done BEFORE number replacement to avoid mangling IP addresses or ports
    urls = extractor.find_urls(text)

    # 4. Standardize extracted URLs for the 'urls' return list
    # This ensures the scan_url function gets the protocol-included version
    processed_urls = [standardize_url(u) for u in urls]

    # 5. Mask URLs with URL token ([URL] gets split to 3 tokens, URL is 1)
    # We sort by length descending to avoid partial replacement (e.g., bit.ly/123 vs bit.ly)
    for u in sorted(urls, key=len, reverse=True):
        text = text.replace(u, " URL ")

    # 6. Clean up HTML residues and extra spaces
    text = re.sub(r"&[a-z0-9#]+;", " ", text)

    # 7. Label driven legacy placeholders replacement
    # If it's spam, we assume it's a 'Big Number' (000). If ham, a 'Small Number' (0).
    placeholder = " 000 " if label == "spam" else " 0 "
    text = re.sub(r"(?i)escape(number|long|url)", placeholder, text)

    # 8. Standard Numeric Masking (Shape-Preserving for modern text)
    # This maintains parity between legacy placeholders and real numbers.'
    text = re.sub(r"\d{3,}", " 000 ", text)
    text = re.sub(r"\d{1,2}", " 0 ", text)

    # FIXME: Sequential regex cannibalizes 3+ digit masks (outputs ' 0 0 ').
    # Left as-is to maintain training parity, as this is a near-harmless bug.
    # The fix:
    # 8. Standard Numeric Masking (Single-Pass Shape-Preserving)
    # Replaces numbers >= 3 digits with ' 000 ', and 1-2 digits with ' 0 '
    # Uses a lambda to prevent sequential regex cannibalization.
    # text = re.sub(
    #     r"\d+",
    #     lambda m: " 000 " if len(m.group(0)) >= 3 else " 0 ",
    #     text
    # )

    # 9. Formatting
    text = re.sub(r"\s+", " ", text).strip()

    return text, processed_urls


def standardize_url(url: str) -> str:
    """
    Standardizes URL to https://domain.tld/path.
    Removes www. to save token space and ensure consistency.
    """
    url = url.strip().lower()
    # Remove existing protocol and www
    clean = re.sub(r"^https?://", "", url)
    clean = re.sub(r"^www\.", "", clean)
    # Re-prefix with https://
    return f"https://{clean}"


def get_tld_tier(domain: str) -> float:
    """
    Categorizes domains into trust tiers based on TLD acquisition friction.

    Returns:
        0.0: High Trust (Legacy & Regulated)
        0.5: Mid Trust (Standard ccTLDs)
        1.0: Low Trust/Suspicious (gTLDs & High-Abuse ccTLDs)
    """
    parts = domain.lower().split(".")
    if len(parts) < 2:
        return 1.0

    tld = parts[-1]

    # Tier 0: Legacy & Highly Regulated
    # These represent the most established and strictly managed namespaces.
    if tld in {"com", "org", "net", "gov", "edu", "mil"}:
        return 0.0

    # Tier 1: Standard Country Codes (ccTLDs)
    # Includes ISO 3166-1 alpha-2 (2-chars), excluding known "free/burner" TLDs.
    high_abuse_cc = {"tk", "ml", "ga", "cf", "gq"}
    if len(tld) == 2 and tld not in high_abuse_cc:
        return 0.5

    # Tier 2: Generic TLDs (gTLDs) & High-Abuse ccTLDs
    # Includes modern gTLDs (.top, .xyz) and the "free" ccTLDs filtered above.
    return 1.0


def calculate_advanced_metadata(url: str) -> np.ndarray:
    """Returns 8-dim structural vector."""
    clean_url = standardize_url(url)
    parsed = urlparse(url if "://" in url else f"http://{url}")
    domain = parsed.netloc
    path = parsed.path
    full_len = len(clean_url)

    # 1. Path Ratio
    path_ratio = len(path) / full_len if full_len > 0 else 0.0
    # 2. TLD Tier
    tld_score = get_tld_tier(domain)
    # 3. Entropy
    prob = [n / len(domain) for n in Counter(domain).values()] if domain else [0]
    entropy = -sum(p * math.log2(p) for p in prob)
    # 4. Dot Count
    dot_count = domain.count(".")
    # 5. Digit Ratio
    digits = sum(c.isdigit() for c in clean_url)
    digit_ratio = digits / full_len if full_len > 0 else 0.0
    # 6. Special Chars
    special_chars = len(re.findall(r"[@\-_?=%]", clean_url))
    # 7. Subdomain Flag
    subdomain_flag = 1.0 if dot_count > 2 else 0.0
    # 8. Path Depth
    path_depth = path.count("/")

    # Scale raw values to prevent gradient dominance (approximate normalization)
    # Entropy max ~4.5, Dot count usually <5, Special chars usually <10, Path depth <5
    return np.array(
        [
            path_ratio,
            tld_score,
            min(entropy / 5.0, 1.0),
            min(dot_count / 5.0, 1.0),
            digit_ratio,
            min(special_chars / 10.0, 1.0),
            subdomain_flag,
            min(path_depth / 5.0, 1.0),
        ],
        dtype=np.float32,
    )

def label_to_risk(label: str) -> float:
    """
    Convert historical labels into binary risk.

    Risk labels:
        spam, scam, phishing, malicious, hazard -> 1.0
        everything else -> 0.0
    """
    if not label:
        return 0.0

    risky_labels = {"spam", "scam", "phishing", "malicious", "fraud", "hazard"}
    return 1.0 if str(label).strip().lower() in risky_labels else 0.0


def probability_confidence(p: float) -> float:
    """
    Confidence based on distance from uncertainty (0.5).

    Formula:
        confidence = 2 * abs(p - 0.5)

    Properties:
        p = 0.5 -> 0.0 (maximum uncertainty)
        p = 0.0 or 1.0 -> 1.0 (maximum confidence)
    """
    p = max(0.0, min(1.0, float(p)))
    return 2.0 * abs(p - 0.5)


def compute_retrieval_signal(top_matches: list[dict], mode: str = "text") -> dict:
    """
    Compute distance-weighted retrieval signal.
    Weighting:
        w_i = exp(semantic_similarity_i) / sum_j exp(semantic_similarity_j)
    Retrieval risk:
        Sum(w_i * label_risk_i)
    Also computes weighted semantic and lexical evidence.
    """
    if not top_matches:
        return {
            "retrieval_risk": 0.0,
            "semantic_risk": 0.0,
            "lexical_risk": 0.0,
            "semantic_confidence": 0.0,
            "lexical_confidence": 0.0,
        }
    # 1. Semantic Voting
    sem_sims = [
        max(0.0, min(1.0, float(m.get("semantic_score", 0.0)))) for m in top_matches
    ]
    sem_exps = [math.exp(s) for s in sem_sims]
    sem_exp_sum = sum(sem_exps) + 1e-9
    sem_weights = [w / sem_exp_sum for w in sem_exps]

    # 2. Lexical Voting
    lex_sims = [
        max(0.0, min(1.0, float(m.get("lexical_score_norm", 0.0)))) for m in top_matches
    ]
    lex_exps = [math.exp(s) for s in lex_sims]
    lex_exp_sum = sum(lex_exps) + 1e-9
    lex_weights = [w / lex_exp_sum for w in lex_exps]

    semantic_risk = 0.0
    lexical_risk = 0.0

    for match, s_weight, l_weight in zip(top_matches, sem_weights, lex_weights):
        label_risk = label_to_risk(match.get("label", ""))
        semantic_risk += s_weight * label_risk
        lexical_risk += l_weight * label_risk

        match["semantic_weight"] = round(s_weight, 4)
        match["lexical_weight"] = round(l_weight, 4)
        match["historical_risk"] = label_risk

    # 3. Dynamic Fusion (Shift from 0.7/0.3 base ratio)
    sem_conf = probability_confidence(semantic_risk)

    # If lexical found absolutely no text overlap, it must abstain entirely (confidence = 0)
    lex_conf = probability_confidence(lexical_risk) if max(lex_sims) > 0.0 else 0.0

    # Dynamic base weights: Text makes more sense with semantic, urls with lexical
    if mode == "url":
        base_sem = 0.30
        base_lex = 0.70
    else:
        base_sem = 0.70
        base_lex = 0.30

    eff_sem = base_sem * sem_conf
    eff_lex = base_lex * lex_conf
    total_eff = eff_sem + eff_lex

    if total_eff > 1e-9:
        retrieval_risk = (semantic_risk * eff_sem + lexical_risk * eff_lex) / total_eff
    else:
        retrieval_risk = base_sem * semantic_risk + base_lex * lexical_risk

    return {
        "retrieval_risk": max(0.0, min(1.0, retrieval_risk)),
        "semantic_risk": max(0.0, min(1.0, semantic_risk)),
        "lexical_risk": max(0.0, min(1.0, lexical_risk)),
        "semantic_confidence": sem_conf,
        "lexical_confidence": lex_conf,
    }


async def scan_text(text: str):
    """
    Retrieval-Augmented Classification (RAC) pipeline for text messages.

    Architecture
    ------------
    1. Feature Extraction: Embeds text into a dense vector space using MiniLM.
    2. Classifier Head: Inference via an ONNX MLP classifier over the embedding.
    3. Retrieval: Fetches top-10 historical records via hybrid HNSW + pg_trgm.
    4. Aggregation: Computes distance-weighted retrieval risk from neighbors.
    5. Heuristics & Rules: Evaluates static regex/keyword rules for an explicit risk floor.
    6. Dynamic Fusion: Blends Classifier, Retrieval, and Rule signals using 3-way confidence weights.
    7. Explainable AI: Generates token-level predictive heatmaps and feature deltas.

    Notes
    -----
    - Uses 'sandwich truncation' and strided rolling windows for long texts.
    - Features a safety override: rules force maximum risk if an high-confidence OTP Scam is detected.
    """

    # ------------------------------------------------------------------
    # 1. Embedding
    # ------------------------------------------------------------------
    vector, xai_ingredients = await get_onnx_embedding(
        text, mode="text", return_xai=True
    )

    # ------------------------------------------------------------------
    # 2. Classifier Head
    # ------------------------------------------------------------------
    input_data = vector.reshape(1, -1).astype(np.float32)
    session = MODEL_REGISTRY["text_classifier"]["session"]

    # XGB head
    output = await asyncio.to_thread(
        session.predict_proba,
        input_data,
    )
    classifier_score = float(output[0][1])  # XGB has hazard = 1
    classifier_score = max(0.0, min(1.0, classifier_score))

    # ------------------------------------------------------------------
    # 3. Retrieval
    # ------------------------------------------------------------------
    top_matches = await hybrid_search_rrf(
        query_text=text,
        query_vector=vector,
        source="text",
        limit=10,
        k=20,
    )

    # ------------------------------------------------------------------
    # 4. Distance-Weighted Retrieval Aggregation
    # ------------------------------------------------------------------
    retrieval = compute_retrieval_signal(top_matches, mode="text")
    retrieval_risk = retrieval["retrieval_risk"]

    # ------------------------------------------------------------------
    # 4.5 Explainable AI & Scam Classification
    # ------------------------------------------------------------------
    # Spam/ham variables to match training script update
    model_score = classifier_score
    ham_score = 1.0 - model_score

    # Explainable AI branch
    explanation_result = explain_text_risk(text)
    rule_boost = explanation_result["total_boost"]
    rule_risk_floor = explanation_result["risk_floor"]
    matched_indicators = explanation_result["matched_indicators"]

    # Classification of scam type
    type_names, type_vectors = await get_scam_type_prototypes()
    scam_classification = await classify_scam_type(
        text=text,
        type_names=type_names,
        type_vectors=type_vectors,
    )

    # ------------------------------------------------------------------
    # 5. Confidence Estimation (3-Way)
    # ------------------------------------------------------------------
    classifier_confidence = probability_confidence(classifier_score)

    # 1. Decisiveness (Linear): Is the retrieval vote clear or 50/50?
    retrieval_decisiveness = probability_confidence(retrieval_risk)

    # 2. Grounding based on intent overlap (Linear base):
    # Raw structural similarity of the best match [0.0 to 1.0]
    # We use the semantic score because natural language relies on paraphrasing.
    top_semantic_score = (
        top_matches[0].get("semantic_score", 0.0) if top_matches else 0.0
    )

    # Cosine similarity can technically be negative, so we clamp it to 0.0 at the floor.
    retrieval_grounding = max(0.0, min(1.0, float(top_semantic_score)))

    # 3. Normalized Confidence: Weighted Geometric Mean (Cube Root of D * G^2)
    # This preserves the non-linear penalty for weak structural matches
    # without unfairly decaying the confidence of strong matches.
    if retrieval_decisiveness == 0.0 or retrieval_grounding == 0.0:
        retrieval_confidence = 0.0
    else:
        product = retrieval_decisiveness * (retrieval_grounding**2)
        retrieval_confidence = math.pow(product, 1.0 / 3.0)

    # Treat the rule_boost as a raw risk indicator.
    # If rule_boost is 0, no heuristics were triggered. We set confidence to 0.0
    # so that the rules engine completely drops out of the dynamic fusion denominator,
    # preventing a "clean" keyword scan from dilution-shielding a dangerous ML score.
    rules_score = rule_boost
    if rules_score == 0:
        # Zero confidence neutralizes this brain's effect on the ensembled average.
        rules_confidence = 0.0
    else:
        # Apply scam-type safety floor - classifier to help
        # If classifier is very confident this is OTP Scam, keep it high risk
        if (
            scam_classification["predicted_type"] == "OTP Scam"
            and scam_classification["confidence_level"] == "high"
        ):
            rules_score = 1.0  # Maximum severity
        rules_confidence = probability_confidence(rules_score)

    # ------------------------------------------------------------------
    # 6. Dynamic Fusion (MLP + DB + Rules)
    # ------------------------------------------------------------------
    base_classifier_weight = 0.35
    base_retrieval_weight = 0.40
    base_rules_weight = 0.25

    effective_classifier_weight = base_classifier_weight * classifier_confidence
    effective_retrieval_weight = base_retrieval_weight * retrieval_confidence
    effective_rules_weight = base_rules_weight * rules_confidence

    total_weight = (
        effective_classifier_weight
        + effective_retrieval_weight
        + effective_rules_weight
    )

    if total_weight > 1e-9:
        final_risk_score = (
            (classifier_score * effective_classifier_weight)
            + (retrieval_risk * effective_retrieval_weight)
            + (rules_score * effective_rules_weight)
        ) / total_weight
    else:
        # All sources are maximally uncertain
        final_risk_score = (
            base_classifier_weight * classifier_score
            + base_retrieval_weight * retrieval_risk
            + base_rules_weight * rules_score
        )

    # ------------------------------------------------------------------
    # 6.5 Scam-Type Safety Floor & Caps
    # ------------------------------------------------------------------
    # Apply the risk floor from the matched indicators
    final_risk_score = max(final_risk_score, rule_risk_floor)

    # Avoid showing absolute 0% or 100% in UI
    final_risk_score = max(final_risk_score, 0.03)
    final_risk_score = min(final_risk_score, 0.97)

    # ------------------------------------------------------------------
    # 7. Decision & Guidance
    # ------------------------------------------------------------------
    if final_risk_score >= 0.75:
        decision = "flagged"
    elif final_risk_score >= 0.55:
        decision = "suspicious"
    else:
        decision = "clear"

    # guidance based on the type of scam
    immediate_guidance = get_prevention_guidance(
        predicted_type=scam_classification["predicted_type"],
        decision=decision,
    )

    # ------------------------------------------------------------------
    # 8. Unified XAI Output (UI + RAC Logs)
    # ------------------------------------------------------------------
    # Only compute if a database match exists
    xai_payload = []
    if top_matches:
        top_match = top_matches[0]
        # 1. Run the XGBoost predictive ablation
        xgb_deltas = compute_loo_deltas(
            unpooled_tokens=xai_ingredients["unpooled_tokens"],
            xgb_model=MODEL_REGISTRY["text_classifier"]["session"],
        )

        # 2. Safe Database Extraction
        doc_embedding_raw = top_match.get("embedding")

        if doc_embedding_raw is not None:
            # Parse the PostgreSQL string back into a Python list
            if isinstance(doc_embedding_raw, str):
                # orjson parses large float arrays 5x-10x faster than standard json
                parsed_list = orjson.loads(doc_embedding_raw)
            else:
                parsed_list = doc_embedding_raw

            doc_embedding = np.array(parsed_list, dtype=np.float32)
        else:
            # If no embeddings, return dummy array to avoid crash
            dim = xai_ingredients["unpooled_tokens"].shape[1]
            doc_embedding = np.zeros(dim, dtype=np.float32)

        # 3. Assemble the Payload
        xai_payload = generate_text_explanation(
            raw_text=text,  # Use request.text if in scan_text()
            offset_mapping=xai_ingredients["offset_mapping"],
            input_ids=xai_ingredients["input_ids"],
            unpooled_tokens=xai_ingredients["unpooled_tokens"],
            doc_embedding=doc_embedding,
            doc_text=top_match.get("clean_text", ""),  # <-- PASS THE RAW TEXT HERE
            xgb_deltas=xgb_deltas,
            mode="text",
        )
    return {
        # --- CORE UI FIELDS ---
        "risk_score": round(final_risk_score, 4),
        "risk_score_percent": round(final_risk_score * 100),
        "decision": decision,
        "scam_type": scam_classification,
        "immediate_guidance": immediate_guidance,
        "input text": text,
        "model_output": {
            "spam_score": round(model_score, 4),
            "ham_score": round(ham_score, 4),
        },
        "explainability": {
            "rule_boost": round(rule_boost, 4),
            "matched_indicators": matched_indicators,
        },
        # --- RAC PIPELINE DEEP LOGS ---
        "sub_scores": {
            "classifier_head": round(classifier_score, 4),
            "retrieval_risk": round(retrieval_risk, 4),
            "retrieval_label": "hazard" if retrieval_risk >= 0.5 else "safe",
            "semantic_vote": round(retrieval["semantic_risk"], 4),
            "lexical_vote": round(retrieval["lexical_risk"], 4),
        },
        "confidence": {
            "classifier": round(classifier_confidence, 4),
            "retrieval": round(retrieval_confidence, 4),
            "rules": round(rules_confidence, 4),
        },
        "fusion_weights": {
            "base": {
                "classifier": base_classifier_weight,
                "retrieval": base_retrieval_weight,
                "rules": base_rules_weight,
            },
            "effective": {
                "classifier": round(effective_classifier_weight, 6),
                "retrieval": round(effective_retrieval_weight, 6),
                "rules": round(effective_rules_weight, 6),
            },
        },
        # --- Explainability ---
        "weightage_explainability": {
            "fusion_breakdown": {
                "effective_xgb_weight": round(
                    effective_classifier_weight / total_weight, 4
                )
                if total_weight > 0
                else 0,
                "effective_db_weight": round(
                    effective_retrieval_weight / total_weight, 4
                )
                if total_weight > 0
                else 0,
                "effective_rules_weight": round(
                    effective_rules_weight / total_weight, 4
                )
                if total_weight > 0
                else 0,
                "db_hallucination_silenced": True
                if retrieval_grounding < 0.1
                else False,
            },
            "token_heatmap": xai_payload,
        },
        "evidence": {
            "retrieval_method": "HNSW (Semantic) + pg_trgm (Lexical) + Dynamic Fusion",
            "match_count": len(top_matches),
            "top_matches": top_matches,
        },
    }


async def scan_url(raw_url: str):
    """
    Retrieval-Augmented Classification (RAC) pipeline for URLs.

    Architecture
    ------------
    1. Safe Resolution: Resolves redirect chains safely with SSRF protection.
    2. Feature Extraction: Extracts URLBERT embeddings and computes 8 structural metadata features.
    3. Classifier Head: Inference via an ONNX MLP over the concatenated embedding + metadata vector.
    4. Retrieval: Fetches top-5 historical malicious URLs using hybrid HNSW + pg_trgm.
    5. Aggregation: Computes distance-weighted retrieval risk from neighbors.
    6. Dynamic Fusion: Blends Classifier and Retrieval signals using a 2-way confidence weight.
    7. Dissonance Check: Audits results if deep learning scores clash heavily with structural priors.
    8. Explainable AI: Extracts metadata SHAP contributions and token-level heatmaps.

    Notes
    -----
    - URLs rely heavily on lexical metrics since phishing variants frequently reuse domain/path structures.
    - The output schema matches the text pipeline to ensure cross-modality frontend compatibility.
    """

    # ------------------------------------------------------------------
    # 1. Safe Resolution (with SSRF protection)
    # ------------------------------------------------------------------
    resolved_url, resolved_successfully = await safe_resolve_redirect(raw_url)

    # Canonicalized URL used for both embedding and retrieval
    stripped_url = standardize_url(resolved_url)

    # ------------------------------------------------------------------
    # 2. Feature Extraction
    # ------------------------------------------------------------------
    # URLBERT embedding (768-dim, already L2-normalized by get_onnx_embedding)
    vector, xai_ingredients = await get_onnx_embedding(
        stripped_url, mode="url", return_xai=True
    )

    # 8 structural features
    meta_vector = calculate_advanced_metadata(resolved_url)

    # ------------------------------------------------------------------
    # 3. Classifier Head (Embedding + Metadata)
    # ------------------------------------------------------------------
    # Concatenate to form 776-dim input
    combined_input = np.concatenate(
        (vector.reshape(1, -1), meta_vector.reshape(1, -1)),
        axis=1,
    ).astype(np.float32)

    session = MODEL_REGISTRY["url_classifier"]["session"]

    # For XGB head
    # predict_proba returns [[prob_safe, prob_hazard]]
    output = await asyncio.to_thread(
        session.predict_proba,
        combined_input,
    )
    # Extract probability of the hazard class (index 1)
    classifier_score = float(output[0][1])  # XGB has hazard = 1
    classifier_score = max(0.0, min(1.0, classifier_score))

    # ------------------------------------------------------------------
    # 3.5 XGBoost Feature Contributions (Metadata)
    # ------------------------------------------------------------------
    # --- XAI Layer: Extract SHAP Values from Pre-Warmed Memory ---
    try:
        # Cascade through Sklearn wrappers (CalibratedClassifierCV -> XGB)
        booster = (
            session.estimator.get_booster()
            if hasattr(session, "estimator")
            else session.get_booster()
        )

        # Native DMatrix conversion for fast C++ execution
        dmat = __import__("xgboost").DMatrix(combined_input)
        contribs = booster.predict(dmat, pred_contribs=True)[0]

        # Topology: (777,) -> 768 text embeddings + 8 metadata + 1 bias
        # Slice indices 768 to 775 to isolate metadata weights
        meta_shap_values = contribs[-9:-1].tolist()
        
    except Exception:
        # Fail-safe fallback if package version mismatches obscure properties
        meta_shap_values = [0.0] * 8       

    # Zip the labels, raw values, and XGBoost SHAP contributions together for the UI
    meta_explanation = [
        {
            "feature": label,
            "raw_value": round(float(val), 4),
            "xgb_contribution": round(float(shap), 4),  # Positive = pushed towards scam
        }
        for label, val, shap in zip(
            [
                "Path Ratio",
                "TLD Tier",
                "Entropy",
                "Dot Count",
                "Digit Ratio",
                "Special Chars",
                "Subdomain Flag",
                "Path Depth",
            ],
            meta_vector,
            meta_shap_values,
        )
    ]

    # ------------------------------------------------------------------
    # 4. Retrieval (HNSW + Hybrid RRF)
    # ------------------------------------------------------------------
    # Important: retrieval uses ONLY the URL embedding, not metadata.
    # This keeps the vector space aligned with what is stored in pgvector.
    top_matches = await hybrid_search_rrf(
        query_text=stripped_url,
        query_vector=vector,
        source="url",
        limit=10,
        k=20,
    )

    # ------------------------------------------------------------------
    # 5. Distance-Weighted Retrieval Aggregation
    # ------------------------------------------------------------------
    # Reuses the same helper as the text pipeline.
    retrieval = compute_retrieval_signal(top_matches, mode="url")
    retrieval_risk = retrieval["retrieval_risk"]

    # ------------------------------------------------------------------
    # 6. Confidence Estimation
    # ------------------------------------------------------------------
    classifier_confidence = probability_confidence(classifier_score)

    # 1. Decisiveness (Linear): Is the retrieval vote clear or 50/50?
    retrieval_decisiveness = probability_confidence(retrieval_risk)

    # 2. Grounding based on STRICT STRUCTURAL OVERLAP (Linear base):
    # Raw structural similarity of the best match [0.0 to 1.0]
    top_lexical_score = (
        top_matches[0].get("lexical_score_raw", 0.0) if top_matches else 0.0
    )
    retrieval_grounding = max(0.0, min(1.0, float(top_lexical_score)))

    # 3. Normalized Confidence: Weighted Geometric Mean (Cube Root of D * G^2)
    # This preserves the non-linear penalty for weak structural matches
    # without unfairly decaying the confidence of strong matches.
    if retrieval_decisiveness == 0.0 or retrieval_grounding == 0.0:
        retrieval_confidence = 0.0
    else:
        product = retrieval_decisiveness * (retrieval_grounding**2)
        retrieval_confidence = math.pow(product, 1.0 / 3.0)

    # ------------------------------------------------------------------
    # 7. Dynamic Fusion
    # ------------------------------------------------------------------
    # Base weights set to 50/50.
    # Because of the grounding factor, Retrieval will only utilize its
    # 50% voting power if it finds a near-perfect structural match.
    base_classifier_weight = 0.50
    base_retrieval_weight = 0.50

    effective_classifier_weight = base_classifier_weight * classifier_confidence
    effective_retrieval_weight = base_retrieval_weight * retrieval_confidence

    total_weight = effective_classifier_weight + effective_retrieval_weight

    if total_weight > 1e-9:
        final_risk_score = (
            classifier_score * effective_classifier_weight
            + retrieval_risk * effective_retrieval_weight
        ) / total_weight
    else:
        # Both sources are maximally uncertain or ungrounded.
        final_risk_score = (
            base_classifier_weight * classifier_score
            + base_retrieval_weight * retrieval_risk
        )

    final_risk_score = max(0.0, min(1.0, float(final_risk_score)))

    # ------------------------------------------------------------------
    # 8. Structural Dissonance Check
    # ------------------------------------------------------------------
    # Compare the final RAC score against a simple structural prior.
    meta_risk_score = float(np.mean(meta_vector))
    dissonance = abs(final_risk_score - meta_risk_score)

    # ------------------------------------------------------------------
    # 9. Decision Logic
    # ------------------------------------------------------------------
    decision = "clear"

    # High-confidence malicious URL
    if final_risk_score > 0.80:
        decision = "flagged"

    # Significant disagreement between RAC and structural heuristics
    elif dissonance > 0.50:
        decision = "audit"

    # ------------------------------------------------------------------
    # 10. XAI Output (Explainable AI)
    # ------------------------------------------------------------------
    # Only compute if a database match exists
    xai_payload = []
    if top_matches:
        top_match = top_matches[0]
        # 1. Run the XGBoost predictive ablation
        xgb_deltas = compute_loo_deltas(
            unpooled_tokens=xai_ingredients["unpooled_tokens"],
            xgb_model=MODEL_REGISTRY["url_classifier"]["session"],
            meta_vector=meta_vector,
        )

        # 2. Safe Database Extraction
        doc_embedding_raw = top_match.get("embedding")

        if doc_embedding_raw is not None:
            # Parse the PostgreSQL string back into a Python list
            if isinstance(doc_embedding_raw, str):
                # orjson parses large float arrays 5x-10x faster than standard json
                parsed_list = orjson.loads(doc_embedding_raw)
            else:
                parsed_list = doc_embedding_raw

            doc_embedding = np.array(parsed_list, dtype=np.float32)
        else:
            # If no embeddings, return dummy array to avoid crash
            dim = xai_ingredients["unpooled_tokens"].shape[1]
            doc_embedding = np.zeros(dim, dtype=np.float32)

        # 3. Assemble the Payload
        xai_payload = generate_text_explanation(
            raw_text=stripped_url,  # Use request.text if in scan_text()
            offset_mapping=xai_ingredients["offset_mapping"],
            input_ids=xai_ingredients["input_ids"],
            unpooled_tokens=xai_ingredients["unpooled_tokens"],
            doc_embedding=doc_embedding,
            doc_text=top_match.get("clean_text", ""),  # <-- PASS THE RAW TEXT HERE
            xgb_deltas=xgb_deltas,
            mode="url",
        )
    return {
        # --- TOP LEVEL DECISION ---
        "risk_score": round(
            final_risk_score, 4
        ),  # Final blended probability (0.0 = Safe, 1.0 = Malicious)
        "decision": decision,  # Threshold action: 'clear', 'audit', or 'flagged'
        # --- URL RESOLUTION ---
        "resolved_url": resolved_url,  # The final destination URL after following safe redirects
        "resolved_successfully": resolved_successfully,  # True if we could reach the end of the redirect chain without hitting an SSRF block
        # --- STRUCTURAL METADATA (Heuristics) ---
        "meta_vector": meta_vector.tolist(),  # Raw values of the 8 structural heuristics
        "meta_labels": [
            "Path Ratio",
            "TLD Tier",
            "Entropy",
            "Dot Count",
            "Digit Ratio",
            "Special Chars",
            "Subdomain Flag",
            "Path Depth",
        ],
        # --- STRUCTURAL DIAGNOSTICS ---
        "meta_risk_score": round(
            meta_risk_score, 4
        ),  # Simple average of the structural heuristic vector
        "dissonance": round(
            dissonance, 4
        ),  # Difference between Deep ML score and Heuristic score. High dissonance (>0.5) triggers an 'audit'
        # --- INDEPENDENT BRAINS (Sub Scores) ---
        "sub_scores": {
            # 1. The Machine Learning Model
            "classifier_head": round(
                classifier_score, 4
            ),  # Raw XGBoost prediction based on Embedding + Metadata
            # 2. The Database Search (Retrieval)
            "retrieval_risk": round(
                retrieval_risk, 4
            ),  # Combined risk based on historical URL neighbors found in the DB
            "retrieval_label": "hazard" if retrieval_risk >= 0.5 else "safe",
            "retrieval_margin": round(
                abs(retrieval_risk - 0.5) * 2, 4
            ),  # Distance from uncertainty. 1.0 = highly certain, 0.0 = totally confused (50/50)
            # 3. How the Database Search Voted
            "semantic_vote": round(
                retrieval["semantic_risk"], 4
            ),  # >0.5 means neighbors with similar 'intent' were mostly scams
            "lexical_vote": round(
                retrieval["lexical_risk"], 4
            ),  # >0.5 means neighbors with similar 'exact characters' were mostly scams
        },
        # --- CONFIDENCE SCORING ---
        "confidence": {
            "classifier": round(
                classifier_confidence, 4
            ),  # How sure the ML model is (low if score is near 0.5)
            "retrieval": round(
                retrieval_confidence, 4
            ),  # How sure the database search is (low if score is near 0.5)
        },
        # --- DYNAMIC FUSION MATH ---
        # Shows exactly how much voting power each brain had in the final risk_score
        "fusion_weights": {
            "base": {
                "classifier": base_classifier_weight,  # Default voting power (40%)
                "retrieval": base_retrieval_weight,  # Default voting power (60%)
            },
            "effective": {
                "classifier": round(
                    effective_classifier_weight, 6
                ),  # Actual voting power after penalizing for low confidence
                "retrieval": round(
                    effective_retrieval_weight, 6
                ),  # Actual voting power after penalizing for low confidence
            },
        },
        # --- Explainability ---
        "explainability": {
            "meta_explanation": meta_explanation,
            "fusion_breakdown": {
                "effective_xgb_weight": round(
                    effective_classifier_weight / total_weight, 4
                )
                if total_weight > 0
                else 0,
                "effective_db_weight": round(
                    effective_retrieval_weight / total_weight, 4
                )
                if total_weight > 0
                else 0,
                "db_hallucination_silenced": True
                if retrieval_grounding < 0.1
                else False,
            },
            "token_heatmap": xai_payload,
        },
        # --- RAW EVIDENCE ---
        "evidence": {
            "retrieval_method": "HNSW (Semantic) + pg_trgm (Lexical) + Dynamic Fusion",
            "aggregation": "softmax(exp(similarity))",
            "match_count": len(
                top_matches
            ),  # Usually 5 (the top 5 closest historical documents)
            "top_matches": top_matches,  # The actual database rows to display to the user/analyst
        },
        # --- ORIGINAL INPUT ---
        "input_url": raw_url,
    }
