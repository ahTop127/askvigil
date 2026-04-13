from tortoise import Tortoise

async def hybrid_search_rrf(query_text: str, query_vector: list[float], limit: int = 5, k: int = 60):
    """
    Executes Hybrid Retrieval using Reciprocal Rank Fusion.
    Combines:
    1. HNSW (pgvector) for Semantic Context
    2. ts_rank (Full-Text Search) for Lexical Keywords
    """
    conn = Tortoise.get_connection("default")
    
    # We use a CTE to rank both sets and then join them
    sql = f"""
    WITH semantic_rank AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY text_embedding <=> %s::vector) as rank
        FROM open_dataset
        ORDER BY text_embedding <=> %s::vector
        LIMIT 50
    ),
    lexical_rank AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(text_search_vector, plainto_tsquery('english', %s)) DESC) as rank
        FROM open_dataset
        WHERE text_search_vector @@ plainto_tsquery('english', %s)
        ORDER BY ts_rank_cd(text_search_vector, plainto_tsquery('english', %s)) DESC
        LIMIT 50
    )
    SELECT 
        COALESCE(s.id, l.id) as id,
        -- The RRF Formula: 1 / (k + rank)
        (COALESCE(1.0 / ({k} + s.rank), 0.0) + COALESCE(1.0 / ({k} + l.rank), 0.0)) as rrf_score,
        o.clean_text,
        o.category
    FROM semantic_rank s
    FULL OUTER JOIN lexical_rank l ON s.id = l.id
    JOIN open_dataset o ON o.id = COALESCE(s.id, l.id)
    ORDER BY rrf_score DESC
    LIMIT %s;
    """
    
    # Parameters for the query
    params = [
        str(query_vector), str(query_vector), # Semantic
        query_text, query_text, query_text,   # Lexical
        limit                                  # Final Limit
    ]
    
    results = await conn.execute_query_dict(sql, params)
    return results