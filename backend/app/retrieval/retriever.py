"""
Phase 4: Retrieval Pipeline
Main Retriever — orchestrates vector search, lexical search, RRF, MMR,
and query embedding. Entry point for all RAG queries.
"""
import asyncio
import logging
from typing import List, Dict, Optional

import httpx

from app.core.config import settings
from app.retrieval.vector_search import VectorSearcher
from app.retrieval.lexical_search import LexicalSearcher
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.mmr import mmr_rerank
from app.retrieval.reranker import Reranker
from app.retrieval.context_expander import ContextExpander

logger = logging.getLogger(__name__)

OPENROUTER_EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings" # Keep for reference but unused

async def embed_query(query: str) -> Optional[List[float]]:
    """Embed a single query string using Gemini API."""
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set — skipping query embedding")
        return None

    raw_model = settings.embedding_model.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{raw_model}:embedContent?key={settings.gemini_api_key}"
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "model": f"models/{raw_model}",
        "content": {"parts": [{"text": query}]},
        "outputDimensionality": settings.embedding_dimension
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            raw = r.json()
            if "embedding" in raw and "values" in raw["embedding"]:
                return raw["embedding"]["values"]
            return None
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
    return None


class Retriever:
    """
    Hybrid RAG retriever.
    1. Embed query
    2. Parallel vector + lexical search
    3. RRF fusion
    4. Optional reranking
    5. Context expansion
    6. MMR diversity reranking
    """

    def __init__(self):
        self.vector = VectorSearcher()
        self.lexical = LexicalSearcher()
        self.reranker = Reranker()
        self.expander = ContextExpander()

    async def retrieve(
        self,
        query: str,
        filter_guest: Optional[str] = None,
        filter_episode_id: Optional[str] = None,
    ) -> Dict:
        """
        Returns a dict with:
          - chunks: final list of context chunks
          - query_embedding: the embedded query vector
          - sources: retrieval metadata for traces
        """
        # 1. Embed query
        query_embedding = await embed_query(query)

        # 2. Parallel search (vector + lexical)
        tasks = []
        if query_embedding:
            tasks.append(
                self.vector.search(
                    query_embedding=query_embedding,
                    top_k=settings.vector_top_k,
                    filter_episode_id=filter_episode_id,
                    filter_guest=filter_guest,
                )
            )
        else:
            tasks.append(asyncio.coroutine(lambda: [])())

        tasks.append(
            self.lexical.search(
                query=query,
                top_k=settings.lexical_top_k,
                filter_guest=filter_guest,
            )
        )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        vector_results = results[0] if not isinstance(results[0], Exception) else []
        lexical_results = results[1] if not isinstance(results[1], Exception) else []

        logger.info(f"Pre-fusion: {len(vector_results)} vector + {len(lexical_results)} lexical")

        # --- COMMENTED OUT TO DIRECTLY SERVE COMBINED VECTOR & LEXICAL RESULTS ---
        # # 3. RRF fusion
        # fused = reciprocal_rank_fusion(
        #     [vector_results, lexical_results],
        #     top_k=settings.fusion_top_k,
        # )
        #
        # # 4. Optional reranking
        # fused = await self.reranker.rerank(query, fused, top_k=settings.rerank_top_k)
        #
        # # 5. Context expansion (if chunk is small)
        # expanded = await self.expander.expand_parent_context(fused)
        #
        # # 6. MMR diversity reranking
        # final_chunks = mmr_rerank(
        #     candidates=expanded,
        #     query_embedding=query_embedding,
        #     top_k=settings.final_context_chunks,
        #     lambda_mult=0.6,
        # )

        # --- DIRECT RETRIEVAL WORKFLOW ---
        # Merge vector and lexical candidates directly
        merged_candidates = []
        seen_ids = set()
        
        # Combine vector results first, then lexical results
        for item in vector_results + lexical_results:
            if item.get("id") and item["id"] not in seen_ids:
                merged_candidates.append(item)
                seen_ids.add(item["id"])

        # Slice to final chunk count limit and apply context parent expansion directly
        direct_sliced = merged_candidates[:settings.final_context_chunks]
        final_chunks = await self.expander.expand_parent_context(direct_sliced)

        # Strip raw embeddings from output (large, not needed by LLM)
        for chunk in final_chunks:
            chunk.pop("embedding", None)

        return {
            "chunks": final_chunks,
            "query_embedding": query_embedding,
            "sources": {
                "vector_count": len(vector_results),
                "lexical_count": len(lexical_results),
                "fused_count": len(merged_candidates),
                "final_count": len(final_chunks),
            },
        }
