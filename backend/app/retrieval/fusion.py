"""
Phase 4: Retrieval Pipeline
Reciprocal Rank Fusion (RRF) to merge vector and lexical result lists.
"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

RRF_K = 60  # Standard RRF constant


def reciprocal_rank_fusion(
    result_lists: List[List[Dict]],
    top_k: int = 20,
    id_field: str = "id",
) -> List[Dict]:
    """
    Merges multiple ranked result lists using Reciprocal Rank Fusion.
    Each list contributes score = 1 / (k + rank) per document.
    Returns top_k unique documents sorted by fused score descending.
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict] = {}

    for result_list in result_lists:
        for rank, doc in enumerate(result_list, start=1):
            doc_id = doc.get(id_field)
            if not doc_id:
                continue
            rrf_score = 1.0 / (RRF_K + rank)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)

    results = []
    for doc_id in sorted_ids[:top_k]:
        doc = doc_map[doc_id].copy()
        doc["rrf_score"] = scores[doc_id]
        results.append(doc)

    logger.info(f"RRF merged {sum(len(r) for r in result_lists)} candidates → {len(results)} unique results")
    return results
