-- This runs EXACTLY ONCE when the database container is first created.
CREATE EXTENSION IF NOT EXISTS vector;

-- Text dataset
CREATE TABLE IF NOT EXISTS open_dataset (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    label VARCHAR(20),
    category VARCHAR(100), -- Added to support your RRF logic
    original_text TEXT,
    clean_text TEXT NOT NULL,
    text_embedding vector(384),
    has_url SMALLINT DEFAULT 0,
    raw_length INTEGER,
    clean_length INTEGER,
    -- Automated Lexical Index
    text_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', clean_text)) STORED
);


-- HNSW for Semantic Search
CREATE INDEX IF NOT EXISTS idx_hnsw_embeddings 
ON open_dataset USING hnsw (text_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- GIN for Lexical Search
CREATE INDEX IF NOT EXISTS idx_gin_lexical ON open_dataset USING GIN (text_search_vector);


-- URL dataset
CREATE TABLE IF NOT EXISTS phishing_url (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    is_malicious BOOLEAN DEFAULT TRUE,
    original_url TEXT NOT NULL,
    resolved_url TEXT,
    domain VARCHAR(255),
    path TEXT,
    preview_title VARCHAR(500),
    url_embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    url_search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(preview_title, '')) || 
        to_tsvector('simple', coalesce(resolved_url, original_url, ''))
    ) STORED
);

-- HNSW for URL Semantic Search
CREATE INDEX IF NOT EXISTS idx_hnsw_url_embeddings 
ON phishing_url USING hnsw (url_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- GIN for URL Lexical Search
CREATE INDEX IF NOT EXISTS idx_gin_url_lexical ON phishing_url USING GIN (url_search_vector);


-- -- Expert Anchors Table
-- CREATE TABLE IF NOT EXISTS centroid_anchors (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(100) UNIQUE NOT NULL,
--     anchor_type VARCHAR(50),
--     vector_data vector(384)
-- );