from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

import logging
from typing import List, Dict
from app.db.client import get_supabase_client

logger = logging.getLogger(__name__)


class ContextExpander:
    """
    Expands the retrieved context to include adjacent chunks (±1 by default)
    from the same episode to build a cohesive local discussion context.
    """

    def __init__(self, window_size: int = 1):
        self.window_size = window_size

    async def expand_parent_context(self, chunks: List[Dict]) -> List[Dict]:
        """
        Conditionally fetches neighboring chunks (chunk_index - 1 .. chunk_index + 1)
        for each retrieved chunk, merging contiguous segments from the same episode.
        """
        if not chunks:
            return []

        logger.info(f"Evaluating context expansion (window=±{self.window_size}) for {len(chunks)} chunks")
        client = get_supabase_client()
        expanded_chunks = []

        for chunk in chunks:
            episode_id = chunk.get("episode_id")
            chunk_index = chunk.get("chunk_index")

            # Fallback if no episode_id or chunk_index available
            if not episode_id or chunk_index is None:
                expanded_chunks.append(chunk)
                continue

            try:
                min_idx = max(0, chunk_index - self.window_size)
                max_idx = chunk_index + self.window_size

                # Query adjacent chunks for this episode
                res = (
                    client.table("transcript_chunks")
                    .select("chunk_index, content, speaker, start_timestamp, end_timestamp")
                    .eq("episode_id", episode_id)
                    .gte("chunk_index", min_idx)
                    .lte("chunk_index", max_idx)
                    .order("chunk_index", desc=False)
                    .execute()
                )

                adjacent = res.data or []
                if not adjacent:
                    expanded_chunks.append(chunk)
                    continue

                # Combine adjacent chunks into a single expanded text block
                combined_content = "\n\n".join(
                    f"[{item.get('speaker') or 'Speaker'}]: {item.get('content', '').strip()}"
                    if item.get('speaker') else item.get('content', '').strip()
                    for item in adjacent
                )

                # Use earliest start timestamp and latest end timestamp
                earliest_ts = adjacent[0].get("start_timestamp") or chunk.get("start_timestamp")
                latest_ts = adjacent[-1].get("end_timestamp") or chunk.get("end_timestamp")

                expanded_chunk = dict(chunk)
                expanded_chunk["content"] = combined_content
                expanded_chunk["start_timestamp"] = earliest_ts
                expanded_chunk["end_timestamp"] = latest_ts
                expanded_chunk["is_expanded"] = True
                expanded_chunks.append(expanded_chunk)

            except Exception as exc:
                logger.warning(f"Context expansion failed for chunk {chunk.get('id')}: {exc}")
                expanded_chunks.append(chunk)

        logger.info(f"Context expansion complete: processed {len(expanded_chunks)} chunks")
        return expanded_chunks
