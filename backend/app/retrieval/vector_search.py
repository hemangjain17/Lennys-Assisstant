"""
Phase 4: Retrieval Pipeline
Dense vector search using the Supabase match_transcript_chunks RPC.
"""
from typing import List, Dict, Optional
import httpx
import logging

from app.db.client import get_supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorSearcher:
    def __init__(self):
        self.client = get_supabase_client()

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = None,
        similarity_threshold: float = None,
        filter_episode_id: Optional[str] = None,
        filter_guest: Optional[str] = None,
    ) -> List[Dict]:
        """
        Calls the match_transcript_chunks Supabase RPC and returns
        a ranked list of chunk dicts with a 'score' field.
        """
        top_k = top_k or settings.vector_top_k
        threshold = similarity_threshold if similarity_threshold is not None else settings.similarity_threshold

        params = {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "similarity_threshold": threshold,
        }
        if filter_episode_id:
            params["filter_episode_id"] = filter_episode_id
        if filter_guest:
            params["filter_guest"] = filter_guest

        try:
            response = self.client.rpc("match_transcript_chunks", params).execute()
            results = []
            for row in response.data or []:
                chunk = row.get("chunk", {})
                chunk["score"] = row.get("similarity", 0.0)
                chunk["episode"] = row.get("episode", {})
                chunk["retrieval_source"] = "vector"
                results.append(chunk)
            logger.info(f"Vector search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
