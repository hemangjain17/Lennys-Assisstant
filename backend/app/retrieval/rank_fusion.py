from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def reciprocal_rank_fusion(
    vector_results: List[Dict],
    lexical_results: List[Dict],
    k: int = 60,
    top_n: int = 20,
    id_key: str = "chunk_id"
) -> List[Dict]:
    """
    Fuses ranked lists using Reciprocal Rank Fusion (RRF).
    RRF score = sum(1 / (k + rank)) for each list where the item appears.
    """
    fusion_scores: Dict[str, float] = {}
    item_map: Dict[str, Dict] = {}

    def process_list(results: List[Dict]):
        for rank, item in enumerate(results):
            item_id = item.get(id_key)
            if not item_id:
                continue
            
            if item_id not in item_map:
                item_map[item_id] = item
                fusion_scores[item_id] = 0.0
                
            fusion_scores[item_id] += 1.0 / (k + rank + 1)

    process_list(vector_results)
    process_list(lexical_results)

    # Sort by RRF score descending
    sorted_items = sorted(
        fusion_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Select top_n items
    fused_results = []
    for item_id, score in sorted_items[:top_n]:
        item = dict(item_map[item_id])
        item["rrf_score"] = score
        fused_results.append(item)

    logger.info(f"RRF fused {len(vector_results)} vector + {len(lexical_results)} lexical into {len(fused_results)} results")
    return fused_results
