-- 010_vector_search.sql
CREATE OR REPLACE FUNCTION match_transcript_chunks(
    query_embedding vector(768),
    match_count int DEFAULT 20,
    similarity_threshold float DEFAULT 0.0,
    filter_episode_id uuid DEFAULT NULL,
    filter_guest text DEFAULT NULL
)
RETURNS TABLE (
    chunk jsonb,
    similarity float,
    episode jsonb,
    metadata jsonb
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$   
BEGIN
    RETURN QUERY
    WITH nearest_chunks AS (
        SELECT
            c.id,
            c.episode_id,
            c.parent_chunk_id,
            c.chunk_index,
            c.content,
            c.speaker,
            c.start_timestamp,
            c.end_timestamp,
            c.token_count,
            c.content_hash,
            c.embedding_model,
            c.embedding_dimension,
            c.embedding_version,
            c.metadata,
            c.created_at,
            (c.embedding <=> query_embedding) AS distance
        FROM transcript_chunks c
        WHERE (filter_episode_id IS NULL OR c.episode_id = filter_episode_id)
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count * 3
    )
    SELECT
        to_jsonb(nc.*) - 'distance' AS chunk,
        (1 - nc.distance)::float AS similarity,
        to_jsonb(e.*) AS episode,
        nc.metadata AS metadata
    FROM nearest_chunks nc
    JOIN episodes e ON nc.episode_id = e.id
    WHERE
        (filter_guest IS NULL OR e.guest ILIKE '%' || filter_guest || '%')
        AND (1 - nc.distance) >= similarity_threshold
    ORDER BY nc.distance ASC
    LIMIT match_count;
END;
$$;
