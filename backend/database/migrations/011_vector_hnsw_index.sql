-- 011_vector_hnsw_index.sql
-- Creates an HNSW vector index on public.transcript_chunks for low-latency cosine similarity search (<=>)

CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
ON public.transcript_chunks 
USING hnsw (embedding vector_cosine_ops);
