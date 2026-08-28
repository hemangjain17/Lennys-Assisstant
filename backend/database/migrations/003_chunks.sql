-- 003_chunks.sql
CREATE TABLE IF NOT EXISTS transcript_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    parent_chunk_id UUID REFERENCES transcript_chunks(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    speaker TEXT,
    start_timestamp TEXT,
    end_timestamp TEXT,
    token_count INTEGER,
    content_hash TEXT NOT NULL,
    embedding vector(768),
    embedding_model TEXT,
    embedding_dimension INTEGER,
    embedding_version TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
