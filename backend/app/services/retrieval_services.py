from tortoise import Tortoise


async def hybrid_search_rrf(
    query_text: str, query_vector: list[float], limit: int = 5, k: int = 60
):
    conn = Tortoise.get_connection("default")

    # Positional parameters ($1, $2) allow multi-reference
    # $1 = query_vector (cast to vector)
    # $2 = query_text (processed by plainto_tsquery)
    # $3 = limit

    sql = f"""
    WITH semantic_rank AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY text_embedding <=> $1::vector) as rank
        FROM open_dataset
        ORDER BY text_embedding <=> $1::vector
        LIMIT 50
    ),
    lexical_rank AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(text_search_vector, plainto_tsquery('english', $2)) DESC) as rank
        FROM open_dataset
        WHERE text_search_vector @@ plainto_tsquery('english', $2)
        ORDER BY rank
        LIMIT 50
    )
    SELECT 
        COALESCE(s.id, l.id) as id,
        (COALESCE(1.0 / ({k} + s.rank), 0.0) + COALESCE(1.0 / ({k} + l.rank), 0.0)) as rrf_score,
        o.clean_text,
        o.category
    FROM semantic_rank s
    FULL OUTER JOIN lexical_rank l ON s.id = l.id
    JOIN open_dataset o ON o.id = COALESCE(s.id, l.id)
    ORDER BY rrf_score DESC
    LIMIT $3;
    """

    # Optimization: Convert vector to string once for asyncpg wire protocol
    vector_str = str(query_vector)

    # Simplified params list
    params = [vector_str, query_text, limit]

    results = await conn.execute_query_dict(sql, params)
    return results
