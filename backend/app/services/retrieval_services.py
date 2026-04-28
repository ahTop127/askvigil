from tortoise import Tortoise


# async def hybrid_search_rrf(
#     query_text: str, query_vector: list[float], limit: int = 5, k: int = 60
# ):
#     conn = Tortoise.get_connection("default")

#     # Positional parameters ($1, $2) allow multi-reference
#     # $1 = query_vector (cast to vector)
#     # $2 = query_text (processed by plainto_tsquery)
#     # $3 = limit

#     sql = f"""
#     WITH semantic_rank AS (
#         SELECT id, ROW_NUMBER() OVER (ORDER BY text_embedding <=> $1::vector) as rank
#         FROM open_dataset
#         ORDER BY text_embedding <=> $1::vector
#         LIMIT 100
#     ),
#     lexical_rank AS (
#         SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(text_search_vector, plainto_tsquery('simple', $2)) DESC) as rank
#         FROM open_dataset
#         WHERE text_search_vector @@ plainto_tsquery('simple', $2)
#         ORDER BY rank
#         LIMIT 100
#     )
#     SELECT
#         COALESCE(s.id, l.id) as id,
#         -- 0.7 Weight for Semantic, 0.3 Weight for Lexical
#         (0.7 * COALESCE(1.0 / ({k} + s.rank), 0.0) +
#         0.3 * COALESCE(1.0 / ({k} + l.rank), 0.0)) as rrf_score,
#         o.clean_text,
#         o.label
#     FROM semantic_rank s
#     FULL OUTER JOIN lexical_rank l ON s.id = l.id
#     JOIN open_dataset o ON o.id = COALESCE(s.id, l.id)
#     ORDER BY rrf_score DESC
#     LIMIT $3;
#     """

#     # Optimization: Convert vector to string once for asyncpg wire protocol
#     vector_str = str(query_vector)

#     # Simplified params list
#     params = [vector_str, query_text, limit]


#     results = await conn.execute_query_dict(sql, params)
#     return results
async def hybrid_search_rrf(
    query_text: str,
    query_vector: list[float],
    source: str = "text",
    limit: int = 5,
    k: int = 60,
):
    conn = Tortoise.get_connection("default")

    # Mapping sources to the verified schema
    source_map = {
        "text": {
            "table": "open_dataset",
            "vector_col": "text_embedding",
            "lexical_col": "text_search_vector",
            # Returns: id, rrf_score, clean_text, label
            "display_cols": "o.clean_text, o.label",
        },
        "url": {
            "table": "phishing_url",
            "vector_col": "url_embedding",
            "lexical_col": "url_search_vector",
            # Aliasing original_url to clean_text and boolean to text label
            # "display_cols": "o.original_url as clean_text, CASE WHEN o.is_malicious THEN 'malicious' ELSE 'safe' END as label"
            "display_cols": """
                COALESCE(o.resolved_url, o.original_url) as clean_text, 
                CASE WHEN o.is_malicious THEN 'malicious' ELSE 'safe' END as label
            """,
        },
    }

    conf = source_map.get(source, source_map["text"])

    sql = f"""
    WITH semantic_rank AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY {conf["vector_col"]} <=> $1::float8[]::vector) as rank
        FROM {conf["table"]}
        ORDER BY {conf["vector_col"]} <=> $1::float8[]::vector
        LIMIT 100
    ),
    lexical_rank AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd({conf["lexical_col"]}, plainto_tsquery('simple', $2)) DESC) as rank
        FROM {conf["table"]}
        WHERE {conf["lexical_col"]} @@ plainto_tsquery('simple', $2)
        ORDER BY rank
        LIMIT 100
    )
    SELECT 
        COALESCE(s.id, l.id) as id,
        (0.7 * COALESCE(1.0 / ({k} + s.rank), 0.0) + 
         0.3 * COALESCE(1.0 / ({k} + l.rank), 0.0)) as rrf_score,
        {conf["display_cols"]}
    FROM semantic_rank s
    FULL OUTER JOIN lexical_rank l ON s.id = l.id
    JOIN {conf["table"]} o ON o.id = COALESCE(s.id, l.id)
    ORDER BY rrf_score DESC
    LIMIT $3;
    """

    clean_vector = (
        query_vector.flatten().tolist()
        if hasattr(query_vector, "tolist")
        else list(query_vector)
    )
    results = await conn.execute_query_dict(sql, [clean_vector, query_text, limit])
    return results
