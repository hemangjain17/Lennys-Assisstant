-- 002_episodes.sql
CREATE TABLE IF NOT EXISTS episodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guest TEXT,
    title TEXT NOT NULL,
    description TEXT,
    publish_date DATE,
    youtube_url TEXT,
    video_id TEXT,
    duration TEXT,
    content_hash TEXT NOT NULL,
    source_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
