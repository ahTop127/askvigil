# docker compose run --rm -v "$(pwd)/backend/resources:/app/resources" backend python scripts/water-stratify-url.py
import csv
import json
import math
import re
from collections import Counter
from urllib.parse import urlparse

import numpy as np
import pandas as pd

INPUT_PATH = "/app/resources/askvigil_master_url_dataset.csv"
OUTPUT_PATH = "/app/resources/askvigil_120k_balanced_hybrid.csv"


# ==========================================
# 1. CORE EXTRACTION LOGIC (PARITY WITH INFERENCE)
# ==========================================
# List of common shorteners to exclude since the system resolves them
SHORTENER_DOMAINS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "is.gd",
    "buff.ly",
    "goo.gl",
    "ow.ly",
    "rebrand.ly",
    "bl.ink",
    "tiny.cc",
    "shorte.st",
    "cutt.ly",
}


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


def is_shortened(url: str) -> bool:
    """Checks if the domain is a known link shortener."""
    parsed = urlparse(url if "://" in url else f"http://{url}")
    domain = parsed.netloc.replace("www.", "")
    return domain in SHORTENER_DOMAINS


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


def extract_unified_features(raw_url: str):
    """
    Returns:
    1. metadata_vector: 8-dim list of floats for MLP training/database.
    2. strat_key: String combining discrete categories for balanced sampling.
    3. raw_length: int
    4. clean_length: int
    """
    raw_url = str(raw_url)
    model_ready_url = standardize_url(raw_url)

    # --- STEP 1: GENERATE METADATA VECTOR (STRICT PARITY) ---
    # We use the raw_url logic from [1] to calculate the 8-dim vector
    vector_np = calculate_advanced_metadata(raw_url)

    # --- STEP 2: GENERATE STRATIFICATION KEY ---
    # Re-use the components for categorization (bins)
    parsed = urlparse(model_ready_url)
    domain = parsed.netloc
    path = parsed.path

    # Extract values for binning (matching logic in [2])
    tld_score = get_tld_tier(domain)
    prob = [n / len(domain) for n in Counter(domain).values()] if domain else [0]
    entropy = -sum(p * math.log2(p) for p in prob)
    path_depth = path.count("/")

    tier_bin = f"T{int(tld_score * 2)}"  # 0.0->T0, 0.5->T1, 1.0->T2
    entropy_bin = "H-Ent" if entropy > 3.5 else "L-Ent"
    depth_bin = "Deep" if path_depth > 2 else "Shallow"
    dot_count = domain.count(".")
    if dot_count <= 1:
        sub_bin = "Base"
    elif dot_count == 2:
        sub_bin = "Sub"
    else:
        sub_bin = "MultiSub"

    strat_key = f"{tier_bin}_{entropy_bin}_{depth_bin}_{sub_bin}"

    # --- STEP 3: PREPARE OUTPUT ---
    raw_length = len(raw_url)
    clean_length = len(model_ready_url)

    # Convert numpy array to list then JSON string for CSV/Pandas compatibility
    metadata_json = json.dumps(vector_np.tolist())

    return metadata_json, strat_key, raw_length, clean_length


# ==========================================
# 2. EXECUTION & WATER-FILLING SAMPLING
# ==========================================

# Load your existing 570k dataset
# Replace with your actual file path
print(f"Loading 570k master dataset from {INPUT_PATH}...")
final_df = pd.read_csv(INPUT_PATH)

# Ensure base columns exist
if "url" not in final_df.columns or "is_malicious" not in final_df.columns:
    raise ValueError("Dataset must contain 'url' and 'is_malicious' columns.")

# --- Filter Shorteners ---
initial_count = len(final_df)
final_df = final_df[~final_df["url"].apply(is_shortened)]
print(f"Filtered {initial_count - len(final_df)} shortened links.")

print("Extracting dual-purpose features (This will take a moment)...")
features = final_df["url"].apply(
    lambda x: pd.Series(
        extract_unified_features(x),
        index=["metadata_vector", "strat_key", "raw_length", "clean_length"],
    )
)
final_df = pd.concat([final_df, features], axis=1)

# Append malicious flag to strat_key to ensure we balance across classes
final_df["strat_key"] = (
    final_df["is_malicious"].astype(str) + "_" + final_df["strat_key"]
)


def balanced_stratified_sample(df, n_total):
    """Water-filling algorithm to ensure rare edge-cases are preserved."""
    counts = df["strat_key"].value_counts(ascending=True)
    sampled_parts = []

    remaining_target = n_total
    remaining_strata = len(counts)

    for key, count in counts.items():
        allocation = remaining_target // remaining_strata
        take = min(allocation, count)

        subset = df[df["strat_key"] == key].sample(n=take, random_state=42)
        sampled_parts.append(subset)

        remaining_target -= take
        remaining_strata -= 1

    result = pd.concat(sampled_parts)

    if len(result) < n_total:
        remaining = df[~df.index.isin(result.index)]
        if not remaining.empty:
            extra = remaining.sample(
                n=min(n_total - len(result), len(remaining)), random_state=42
            )
            result = pd.concat([result, extra])

    return result.sample(frac=1, random_state=42).reset_index(drop=True)


print("Executing Water-Filling Stratification...")
TARGET_ROWS = 120_000
TARGET_PER_CLASS = TARGET_ROWS // 2

malicious_df = final_df[final_df["is_malicious"] == True]
benign_df = final_df[final_df["is_malicious"] == False]

df_50k = (
    pd.concat(
        [
            balanced_stratified_sample(malicious_df, TARGET_PER_CLASS),
            balanced_stratified_sample(benign_df, TARGET_PER_CLASS),
        ]
    )
    .sample(frac=1, random_state=42)
    .reset_index(drop=True)
)

# ==========================================
# 3. EXPORT FOR DATABASE SEEDING
# ==========================================
# 1. Apply the cleaning to the URL column itself
df_50k["url"] = df_50k["url"].apply(standardize_url)
df_50k["metadata_vector"] = df_50k["metadata_vector"].apply(
    lambda x: x.replace('"', "") if isinstance(x, str) else x
)

# 2. Select columns (now 'url' contains the stripped version)
export_cols = ["url", "is_malicious", "raw_length", "clean_length", "metadata_vector"]
df_50k_final = df_50k[export_cols]

df_50k_final.to_csv(
    OUTPUT_PATH,
    index=False,
    sep=",",
    quoting=csv.QUOTE_NONNUMERIC,  # Automatically quotes all non-numeric strings
    quotechar='"',
    doublequote=True,
    encoding="utf-8",  # Force standard UTF-8 (no BOM)
)

print(f"Success. Balanced dataset exported to {OUTPUT_PATH}")
print(f"Label distribution:\n{df_50k_final['is_malicious'].value_counts()}")
