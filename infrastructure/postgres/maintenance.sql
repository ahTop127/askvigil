-- maintenance.sql

-- 1. DROP: Remove indexes to allow high-speed bulk ingestion
DROP INDEX IF EXISTS idx_hnsw_embeddings;
DROP INDEX IF EXISTS idx_gin_lexical;

-- [RUN INGESTION HERE]

-- 2. REBUILD: Restore architectural state
-- Vector Index (HNSW)
CREATE INDEX idx_hnsw_embeddings 
ON open_dataset 
USING hnsw (text_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Lexical Index (GIN)
CREATE INDEX idx_gin_lexical 
ON open_dataset 
USING GIN (text_search_vector);

-- Metadata Filter Index
CREATE INDEX idx_open_dataset_metadata 
ON open_dataset (source, has_url, raw_length, clean_length);