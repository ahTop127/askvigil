-- DROP: Remove the index to allow high-speed bulk ingestion
DROP INDEX IF EXISTS idx_hnsw_embeddings;

-- CREATE: Rebuild the index after ingestion is complete
-- Optimized for ARM Neoverse N1 (24GB RAM instance)
CREATE INDEX idx_hnsw_embeddings 
ON open_dataset 
USING hnsw (text_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);