"""
Phase 4: Retrieval Pipeline
Full-text lexical search using PostgreSQL tsvector / GIN index on Supabase.
"""
from typing import List, Dict, Optional
import logging

from app.db.client import get_supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class LexicalSearcher:
    def __init__(self):
        self.client = get_supabase_client()

    async def search(
        self,
        query: str,
        top_k: int = None,
        filter_guest: Optional[str] = None,
    ) -> List[Dict]:
        """
        Uses PostgreSQL full-text search (tsvector GIN index) on the
        transcript_chunks table. Returns chunks with a 'score' field
        based on ts_rank.
        """
        top_k = top_k or settings.lexical_top_k

        try:
            # Build the base query using Supabase PostgREST text search
            q = (
                self.client.table("transcript_chunks")
                .select("*, episodes!inner(guest, title, youtube_url)")
                .limit(top_k)
            )
            if filter_guest:
                q = q.ilike("episodes.guest", f"%{filter_guest}%")

            try:
                response = q.text_search("fts", query, options={"type": "web_search", "config": "english"}).execute()
            except Exception:
                # Re-build query for content search if fts column does not exist
                q2 = (
                    self.client.table("transcript_chunks")
                    .select("*, episodes!inner(guest, title, youtube_url)")
                    .limit(top_k)
                )
                if filter_guest:
                    q2 = q2.ilike("episodes.guest", f"%{filter_guest}%")
                response = q2.text_search("content", query, options={"type": "web_search", "config": "english"}).execute()
            results = []
            for row in response.data or []:
                episode_data = row.pop("episodes", {})
                row["score"] = 1.0  # Lexical results don't have a numeric rank from PostgREST
                row["episode"] = episode_data
                row["retrieval_source"] = "lexical"
                results.append(row)

            logger.info(f"Lexical search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Lexical search failed: {e}")
            return []
