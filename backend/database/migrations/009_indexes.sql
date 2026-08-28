-- 009_indexes.sql
CREATE INDEX IF NOT EXISTS idx_chunks_episode_id ON transcript_chunks(episode_id);
CREATE INDEX IF NOT EXISTS idx_chunks_parent_chunk_id ON transcript_chunks(parent_chunk_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);

-- Full text search indexes (PostgreSQL Lexical Search)
ALTER TABLE transcript_chunks ADD COLUMN IF NOT EXISTS fts tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(speaker, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B')
) STORED;

CREATE INDEX IF NOT EXISTS idx_chunks_fts ON transcript_chunks USING GIN (fts);

-- Vector index (HNSW)
-- Gemini Embeddings → 768 dimensions
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON transcript_chunks USING hnsw (embedding vector_cosine_ops);
