-- This runs EXACTLY ONCE when the database container is first created.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS open_dataset (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    label VARCHAR(20),
    category VARCHAR(100), -- Added to support your RRF logic
    original_text TEXT,
    clean_text TEXT UNIQUE NOT NULL,
    text_embedding vector(384),
    -- Automated Lexical Index
    text_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', clean_text)) STORED
);


-- HNSW for Semantic Search
CREATE INDEX IF NOT EXISTS idx_hnsw_embeddings 
ON open_dataset USING hnsw (text_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- GIN for Lexical Search
CREATE INDEX IF NOT EXISTS idx_gin_lexical ON open_dataset USING GIN (text_search_vector);

-- -- Expert Anchors Table
-- CREATE TABLE IF NOT EXISTS centroid_anchors (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(100) UNIQUE NOT NULL,
--     anchor_type VARCHAR(50),
--     vector_data vector(384)
-- );