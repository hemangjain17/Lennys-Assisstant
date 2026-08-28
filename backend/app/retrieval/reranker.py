import httpx
import logging
from typing import List, Dict, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class Reranker:
    """
    Reranks hybrid search candidates using Voyage AI or Cohere Cross-Encoder models.
    Supports model 'voyage-4-lite', 'rerank-2', 'rerank-v3.5', etc.
    """

    def __init__(self):
        self.cohere_key = settings.cohere_api_key
        self.voyage_key = settings.voyageai_api_key
        self.provider = (settings.reranker_provider or "").lower()
        self.model_name = settings.reranker_model_name or "voyage-4-lite"
        self.enabled = settings.reranker_enabled or bool(self.cohere_key or self.voyage_key)

    async def _rerank_voyage(self, query: str, docs: List[str], candidates: List[Dict], top_k: int) -> List[Dict]:
        url = "https://api.voyageai.com/v1/rerank"
        headers = {
            "Authorization": f"Bearer {self.voyage_key}",
            "Content-Type": "application/json",
        }
        # Voyage AI rerank models: rerank-2, rerank-2-lite
        model = self.model_name if "rerank-2" in self.model_name else "rerank-2"
        payload = {
            "model": model,
            "query": query,
            "documents": docs,
            "top_k": min(top_k, len(candidates)),
        }

        try:
            logger.info(f"Reranking {len(candidates)} candidates via Voyage AI ({model})")
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            results = data.get("data", [])
            reranked = []
            for item in results:
                idx = item.get("index")
                score = item.get("relevance_score", 0.0)
                if idx is not None and 0 <= idx < len(candidates):
                    cand = dict(candidates[idx])
                    cand["rerank_score"] = score
                    reranked.append(cand)

            logger.info(f"Voyage AI reranked {len(candidates)} candidates → top {len(reranked)}")
            return reranked if reranked else candidates[:top_k]

        except Exception as exc:
            logger.warning(f"Voyage AI reranking failed: {exc}. Falling back to Cohere or original order.")
            if self.cohere_key:
                return await self._rerank_cohere(query, docs, candidates, top_k)
            return candidates[:top_k]

    async def _rerank_cohere(self, query: str, docs: List[str], candidates: List[Dict], top_k: int) -> List[Dict]:
        url = "https://api.cohere.com/v2/rerank"
        headers = {
            "Authorization": f"Bearer {self.cohere_key}",
            "Content-Type": "application/json",
        }
        model = self.model_name if "cohere" in self.provider or "rerank-v" in self.model_name else "rerank-v3.5"
        payload = {
            "model": model,
            "query": query,
            "documents": docs,
            "top_n": min(top_k, len(candidates)),
        }

        try:
            logger.info(f"Reranking {len(candidates)} candidates via Cohere ({model})")
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    v1_url = "https://api.cohere.com/v1/rerank"
                    response = await client.post(v1_url, headers=headers, json=payload)

                response.raise_for_status()
                data = response.json()

            results = data.get("results", [])
            reranked = []
            for item in results:
                idx = item.get("index")
                score = item.get("relevance_score", 0.0)
                if idx is not None and 0 <= idx < len(candidates):
                    cand = dict(candidates[idx])
                    cand["rerank_score"] = score
                    reranked.append(cand)

            logger.info(f"Cohere reranked {len(candidates)} candidates → top {len(reranked)}")
            return reranked if reranked else candidates[:top_k]

        except Exception as exc:
            logger.warning(f"Cohere reranking failed: {exc}. Falling back to pre-rerank order.")
            return candidates[:top_k]

    async def rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        if not candidates:
            return []

        docs = [c.get("content", "").strip() for c in candidates]
        if not any(docs):
            return candidates[:top_k]

        # Route based on key / provider / model name
        if self.voyage_key or "voyage" in self.provider or "voyage" in self.model_name:
            if self.voyage_key:
                return await self._rerank_voyage(query, docs, candidates, top_k)

        if self.cohere_key or "cohere" in self.provider:
            return await self._rerank_cohere(query, docs, candidates, top_k)

        logger.info("No reranker API key provided — bypassing cross-encoder reranking")
        return candidates[:top_k]
