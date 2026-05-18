from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from .search_engine import keyword_search, semantic_search


def reciprocal_rank_fusion(
    ranked_lists: List[List[str]],
    k: int = 60,
) -> Dict[str, float]:
    """Compute RRF scores for document IDs across multiple ranked lists.

    score(d) = sum over lists of 1 / (k + rank(d))
    """
    scores: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores


def hybrid_search(
    query: str,
    df: pd.DataFrame,
    n_results: int = 5,
    k: int = 60,
    where: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """Combine keyword and semantic search via Reciprocal Rank Fusion.

    Returns a merged, re-ranked result list with keys:
      name, rrf_score, keyword_rank, semantic_rank, listeners, source.
    """
    kw_results = keyword_search(query, df, n_results=n_results * 2)
    sem_results = semantic_search(query, n_results=n_results * 2, where=where)

    kw_ids = [r["name"] for r in kw_results]
    sem_ids = [r["metadata"].get("name", r["id"]) for r in sem_results]

    rrf_scores = reciprocal_rank_fusion([kw_ids, sem_ids], k=k)

    kw_rank_map = {name: i + 1 for i, name in enumerate(kw_ids)}
    sem_rank_map = {name: i + 1 for i, name in enumerate(sem_ids)}

    sem_meta_map = {
        r["metadata"].get("name", r["id"]): r["metadata"]
        for r in sem_results
    }
    kw_meta_map = {r["name"]: r for r in kw_results}

    merged: List[Dict[str, Any]] = []
    for name, score in sorted(rrf_scores.items(), key=lambda x: -x[1]):
        meta = sem_meta_map.get(name, kw_meta_map.get(name, {}))
        listeners = meta.get("listeners", None) if isinstance(meta, dict) else None
        source = meta.get("source_collection", "") if isinstance(meta, dict) else ""
        merged.append({
            "name": name,
            "rrf_score": round(score, 6),
            "keyword_rank": kw_rank_map.get(name, None),
            "semantic_rank": sem_rank_map.get(name, None),
            "listeners": listeners,
            "source": source,
        })
        if len(merged) >= n_results:
            break

    return merged


def print_hybrid_comparison(
    query: str,
    df: pd.DataFrame,
    n_results: int = 5,
    k: int = 60,
) -> None:
    """Print keyword, semantic, and hybrid results side by side for a query."""
    print(f"\n{'='*65}")
    print(f"Hybrid Search Comparison — Query: \"{query}\"")
    print(f"{'='*65}")

    kw = keyword_search(query, df, n_results=n_results)
    sem = semantic_search(query, n_results=n_results)
    hyb = hybrid_search(query, df, n_results=n_results, k=k)

    print(f"\n{'KEYWORD':<25} {'SEMANTIC':<25} {'HYBRID (RRF)':<25}")
    print("-" * 75)
    max_len = max(len(kw), len(sem), len(hyb))
    for i in range(max_len):
        kw_name = kw[i]["name"][:22] if i < len(kw) else ""
        sem_name = sem[i]["metadata"].get("name", sem[i]["id"])[:22] if i < len(sem) else ""
        hyb_name = hyb[i]["name"][:22] if i < len(hyb) else ""
        print(f"{kw_name:<25} {sem_name:<25} {hyb_name:<25}")
