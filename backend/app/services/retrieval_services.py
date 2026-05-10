# ============================================================================
# retrieval-service.py
# ============================================================================
# Retrieval-Augmented Classification (RAC) Support Functions
#
# Retrieval:
#   - Semantic search (HNSW / pgvector)
#   - Lexical search (Trigram character similarity via pg_trgm)
#   - Reciprocal Rank Fusion (RRF)
#
# RAC Enhancements:
#   - Raw cosine similarity returned for every candidate
#   - Raw trigram similarity returned for every candidate (natively 0.0 to 1.0)
# ============================================================================

from tortoise import Tortoise
from app.core.config import settings
import re

def prepare_text_for_lexical(query: str) -> str:
    """
    Strips common English stop words and structural noise.
    This prevents Trigrams from matching irrelevant 'ham' emails 
    just because they both use words like 'the', 'you', or 'and'.
    """
    if not isinstance(query, str) or not query.strip():
        return ""

    # Hardcoded set of top English stop words + RAC structural noise
    # (Using a set provides O(1) lightning-fast lookups)
    stop_words = {
        "a", "about", "all", "am", "an", "and", "any", "are", "as", "at", "be",
        "been", "but", "by", "can", "could", "do", "did", "for", "from", "has",
        "have", "had", "he", "her", "his", "how", "i", "if", "in", "is", "it",
        "its", "me", "my", "not", "of", "on", "or", "our", "out", "so", "that",
        "the", "their", "them", "then", "there", "these", "they", "this", "to",
        "up", "us", "was", "we", "what", "when", "where", "which", "who", "will",
        "with", "would", "you", "your", "yours",
        # Legacy noise
        "url", "0", "000"
    }

    tokens = [
        token for token in query.split()
        if token.strip().lower() not in stop_words
    ]
    return " ".join(tokens).strip()


def prepare_url_for_lexical(url: str) -> str:
    """
    Converts a URL into a token-friendly text representation and 
    strips 'URL Stop Words' (TLDs and boilerplate) to maximize Trigram accuracy.
    """
    if not isinstance(url, str) or not url.strip():
        return ""
    
    def standardize_url(url: str) -> str:
        url = url.strip().lower()
        clean = re.sub(r"^https?://", "", url)
        clean = re.sub(r"^www\.", "", clean)
        return f"https://{clean}"

    clean = standardize_url(url)
    clean = re.sub(r"^https://", "", clean)
    clean = clean.replace("/", " ").replace(".", " ").replace("-", " ").replace("_", " ")
    clean = re.sub(r"[^a-z0-9\s]", " ", clean)
    
    # URL Boilerplate "Stop Words"
    url_stop_words = {
        "com", "org", "net", "co", "us", "uk", "info", "biz",
        "www", "html", "htm", "php", "asp", "aspx", "jsp", "index"
    }

    tokens = [
        token for token in clean.split()
        if token.strip() not in url_stop_words
    ]
    
    return " ".join(tokens).strip()


async def semantic_search(query_vector: list[float], source: str = "text", limit: int = 10):
    """Pure semantic search."""
    conn = Tortoise.get_connection("default")

    source_map = {
        "text": {
            "table": "open_dataset",
            "vector_col": "text_embedding",
            "display_cols": "o.clean_text, o.label",
        },
        "url": {
            "table": "phishing_url",
            "vector_col": "url_embedding",
            "display_cols": """
                COALESCE(o.resolved_url, o.original_url) AS clean_text,
                CASE WHEN o.is_malicious THEN 'malicious' ELSE 'safe' END AS label
            """,
        },
    }

    conf = source_map.get(source, source_map["text"])
    expected_dims = settings.DIM_TEXT if source == "text" else settings.DIM_URL
    actual_dims = len(query_vector)

    if actual_dims != expected_dims:
        raise ValueError(
            f"Dimension mismatch for source '{source}': "
            f"Expected {expected_dims}, got {actual_dims}"
        )

    sql = f"""
    SELECT
        o.id,
        (1.0 - (o.{conf["vector_col"]} <=> $1::float8[]::vector)) AS semantic_score,
        {conf["display_cols"]}
    FROM {conf["table"]} o
    ORDER BY o.{conf["vector_col"]} <=> $1::float8[]::vector
    LIMIT $2;
    """

    clean_vector = query_vector.flatten().tolist() if hasattr(query_vector, "tolist") else list(query_vector)
    return await conn.execute_query_dict(sql, [clean_vector, limit])


async def lexical_search(query_text: str, source: str = "text", limit: int = 10):
    """Pure lexical search using pg_trgm similarity."""
    conn = Tortoise.get_connection("default")

    source_map = {
        "text": {
            "table": "open_dataset",
            "compare_col": "o.clean_text",
            "display_cols": "o.clean_text, o.label",
        },
        "url": {
            "table": "phishing_url",
            "compare_col": "COALESCE(o.resolved_url, o.original_url)",
            "display_cols": """
                COALESCE(o.resolved_url, o.original_url) AS clean_text,
                CASE WHEN o.is_malicious THEN 'malicious' ELSE 'safe' END AS label
            """,
        },
    }

    conf = source_map.get(source, source_map["text"])
    
    lexical_query = prepare_url_for_lexical(query_text) if source == "url" else prepare_text_for_lexical(query_text)
    if not lexical_query:
        lexical_query = query_text

    # Uses the pg_trgm '%' operator (index supported) or directly orders by similarity
    sql = f"""
    SELECT
        o.id,
        similarity({conf["compare_col"]}, $1) AS lexical_score_raw,
        {conf["display_cols"]}
    FROM {conf["table"]} o
    WHERE {conf["compare_col"]} % $1
    ORDER BY lexical_score_raw DESC
    LIMIT $2;
    """

    rows = await conn.execute_query_dict(sql, [lexical_query, limit])

    for row in rows:
        # pg_trgm natively returns a float between 0.0 and 1.0! 
        # No BM25 normalizations/pivots required.
        row["lexical_score_norm"] = float(row.get("lexical_score_raw", 0.0))

    return rows


async def hybrid_search_rrf(
    query_text: str,
    query_vector: list[float],
    source: str = "text",
    limit: int = 10,
    k: int = 60,
):
    """
    Hybrid retrieval using:
        - HNSW semantic candidate generation (Top 1000)
        - Trigram Lexical rescoring on the candidate pool
        - Reciprocal Rank Fusion (RRF)
    """
    conn = Tortoise.get_connection("default")

    source_map = {
        "text": {
            "table": "open_dataset",
            "vector_col": "text_embedding",
            "compare_col": "o.clean_text",
            "display_cols": "o.clean_text, o.label",
        },
        "url": {
            "table": "phishing_url",
            "vector_col": "url_embedding",
            "compare_col": "COALESCE(o.resolved_url, o.original_url)",
            "display_cols": """
                COALESCE(o.resolved_url, o.original_url) AS clean_text,
                CASE WHEN o.is_malicious THEN 'malicious' ELSE 'safe' END AS label
            """,
        },
    }

    conf = source_map.get(source, source_map["text"])
    expected_dims = settings.DIM_TEXT if source == "text" else settings.DIM_URL
    actual_dims = len(query_vector)

    if actual_dims != expected_dims:
        raise ValueError(
            f"Dimension mismatch for source '{source}': "
            f"Expected {expected_dims}, got {actual_dims}"
        )
        
    # Dedicated lexical query preprocessing
    if source == "url":
        lexical_query = prepare_url_for_lexical(query_text)
        w_sem, w_lex = 0.3, 0.7  # Lexical is king for URLs
    else:
        lexical_query = prepare_text_for_lexical(query_text)
        w_sem, w_lex = 0.7, 0.3  # Semantic is king for Text

    if not lexical_query:
        lexical_query = query_text

    sql = f"""
    WITH semantic_candidates AS (
        SELECT
            o.id,
            (1.0 - (o.{conf["vector_col"]} <=> $1::float8[]::vector)) AS semantic_score,
            {conf["compare_col"]} AS raw_compare_text,
            {conf["display_cols"]}
        FROM {conf["table"]} o
        ORDER BY o.{conf["vector_col"]} <=> $1::float8[]::vector
        LIMIT 1000 -- Fetch top 1000 conceptual matches
    ),
    scored_candidates AS (
        SELECT
            id,
            semantic_score,
            ROW_NUMBER() OVER (ORDER BY semantic_score DESC) as semantic_rank,
            similarity(raw_compare_text, $2) AS lexical_score_raw,
            ROW_NUMBER() OVER (ORDER BY similarity(raw_compare_text, $2) DESC) as lexical_rank,
            clean_text,
            label
        FROM semantic_candidates
    )
    SELECT
        id,
        (
            {w_sem} * COALESCE(1.0 / ({k} + semantic_rank), 0.0) +
            {w_lex} * COALESCE(1.0 / ({k} + lexical_rank), 0.0)
        ) AS rrf_score,
        semantic_score,
        lexical_score_raw,
        lexical_score_raw AS lexical_score_norm, -- Trigrams are natively 0.0 to 1.0!
        clean_text,
        label
    FROM scored_candidates
    ORDER BY rrf_score DESC
    LIMIT $3;
    """

    clean_vector = query_vector.flatten().tolist() if hasattr(query_vector, "tolist") else list(query_vector)
    rows = await conn.execute_query_dict(sql, [clean_vector, lexical_query, limit])

    return rows