-- This runs EXACTLY ONCE when the database container is first created.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

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
);


-- HNSW for Semantic Search
CREATE INDEX IF NOT EXISTS idx_hnsw_embeddings 
ON open_dataset USING hnsw (text_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Gin Trigram Index for Lexical Search
CREATE INDEX IF NOT EXISTS idx_trgm_clean_text 
ON open_dataset USING GIN (clean_text gin_trgm_ops);

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
    raw_length INTEGER,
    clean_length INTEGER,
    url_embedding vector(768),
    metadata_vector vector(8),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
);

-- HNSW for URL Semantic Search
CREATE INDEX IF NOT EXISTS idx_hnsw_url_embeddings 
ON phishing_url USING hnsw (url_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- GIN Trigram Index for URL Lexical Search
CREATE INDEX IF NOT EXISTS idx_trgm_url 
ON phishing_url USING GIN (coalesce(resolved_url, original_url) gin_trgm_ops);

-- -- Expert Anchors Table
-- CREATE TABLE IF NOT EXISTS centroid_anchors (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(100) UNIQUE NOT NULL,
--     anchor_type VARCHAR(50),
--     vector_data vector(384)
-- );


-- Scam Cases Table
CREATE TABLE IF NOT EXISTS scam_cases (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(512),
    url_link VARCHAR(512),
    scam_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    news_date DATE NOT NULL
);

-- Indexes for filtering and classification dimensions
CREATE INDEX IF NOT EXISTS idx_scam_cases_scam_type ON scam_cases(scam_type);
CREATE INDEX IF NOT EXISTS idx_scam_cases_platform ON scam_cases(platform);
CREATE INDEX IF NOT EXISTS idx_scam_cases_news_date ON scam_cases(news_date);