"""
Phase 4: Retrieval Pipeline
Maximum Marginal Relevance (MMR) for diversity-aware reranking.
Reduces redundant chunks from the same episode/speaker before final context injection.
"""
from typing import List, Dict, Optional
import math
import logging

logger = logging.getLogger(__name__)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def mmr_rerank(
    candidates: List[Dict],
    query_embedding: Optional[List[float]],
    top_k: int = 10,
    lambda_mult: float = 0.5,
    embedding_field: str = "embedding",
    score_field: str = "rrf_score",
) -> List[Dict]:
    """
    MMR selects documents that are both relevant (high score) and diverse
    (low similarity to already-selected documents).

    lambda_mult=1.0 → pure relevance (no diversity)
    lambda_mult=0.0 → pure diversity (no relevance)
    lambda_mult=0.5 → balanced (default)

    Falls back to score-sorted order if embeddings are not present.
    """
    if not candidates:
        return []

    # Check if embeddings are available for MMR
    has_embeddings = all(
        isinstance(doc.get(embedding_field), list) and len(doc[embedding_field]) > 0
        for doc in candidates
    )

    if not has_embeddings or query_embedding is None:
        logger.warning("MMR: embeddings unavailable, falling back to score sort")
        return sorted(candidates, key=lambda d: d.get(score_field, 0), reverse=True)[:top_k]

    selected: List[Dict] = []
    remaining = candidates.copy()

    while len(selected) < top_k and remaining:
        if not selected:
            # First pick: highest relevance score
            best = max(remaining, key=lambda d: d.get(score_field, 0))
        else:
            # MMR: balance relevance vs. similarity to already-selected
            selected_embeddings = [s[embedding_field] for s in selected]
            best = None
            best_score = float("-inf")
            for doc in remaining:
                doc_emb = doc[embedding_field]
                relevance = cosine_similarity(query_embedding, doc_emb)
                max_sim = max(cosine_similarity(doc_emb, sel_emb) for sel_emb in selected_embeddings)
                mmr_score = lambda_mult * relevance - (1 - lambda_mult) * max_sim
                if mmr_score > best_score:
                    best_score = mmr_score
                    best = doc

        selected.append(best)
        remaining.remove(best)

    logger.info(f"MMR selected {len(selected)} diverse chunks from {len(candidates)} candidates")
    return selected
