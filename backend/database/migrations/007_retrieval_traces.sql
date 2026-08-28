-- 007_retrieval_traces.sql
CREATE TABLE IF NOT EXISTS retrieval_traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    original_query TEXT,
    rewritten_query TEXT,
    subqueries JSONB,
    strategy TEXT,
    candidate_count INTEGER,
    selected_chunks JSONB,
    latencies JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 008_evaluation.sql
CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT,
    category TEXT,
    retrieval_metrics JSONB,
    generation_metrics JSONB,
    latency_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
