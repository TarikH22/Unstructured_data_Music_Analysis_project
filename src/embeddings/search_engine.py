from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from .chroma_store import get_client, get_or_create_collection, query_collection, COLLECTION_NAME


def semantic_search(
    query: str,
    n_results: int = 5,
    where: Optional[Dict] = None,
    collection_name: str = COLLECTION_NAME,
) -> List[Dict[str, Any]]:
    """Search artists by meaning using ChromaDB.

    Returns a ranked list of result dicts (id, document, metadata, distance, similarity).
    """
    client = get_client()
    collection = get_or_create_collection(client, name=collection_name)
    results = query_collection(collection, [query], n_results=n_results, where=where)
    return results[0]


def keyword_search(
    query: str,
    df: pd.DataFrame,
    text_columns: Optional[List[str]] = None,
    n_results: int = 5,
    case: bool = False,
) -> List[Dict[str, Any]]:
    """Exact keyword search over DataFrame text columns.

    Returns a list of result dicts with keys: name, matched_column, snippet.
    """
    if text_columns is None:
        text_columns = [c for c in ["name", "description", "source_collection", "url"] if c in df.columns]

    hits: List[Dict[str, Any]] = []
    seen_names: set = set()

    for col in text_columns:
        if col not in df.columns:
            continue
        mask = df[col].astype(str).str.contains(query, case=case, na=False, regex=False)
        for _, row in df[mask].iterrows():
            name = str(row.get("name", ""))
            if name in seen_names:
                continue
            seen_names.add(name)
            hits.append({
                "name": name,
                "matched_column": col,
                "snippet": str(row[col])[:120],
                "source_collection": str(row.get("source_collection", "")),
                "listeners": row.get("listeners", None),
            })
            if len(hits) >= n_results:
                return hits

    return hits


def compare_search(
    query: str,
    df: pd.DataFrame,
    n_results: int = 5,
    where: Optional[Dict] = None,
) -> Dict[str, List]:
    """Run both keyword and semantic search and return results side by side."""
    print(f"\n{'='*60}")
    print(f"Query: \"{query}\"")
    print(f"{'='*60}")

    kw = keyword_search(query, df, n_results=n_results)
    sem = semantic_search(query, n_results=n_results, where=where)

    print(f"\n--- KEYWORD SEARCH ({len(kw)} results) ---")
    if kw:
        for i, r in enumerate(kw, 1):
            listeners = r.get("listeners")
            l_str = f"{int(float(listeners)):,}" if listeners and pd.notna(listeners) else "N/A"
            print(f"  {i}. {r['name']}  [col={r['matched_column']}]  listeners={l_str}")
    else:
        print("  (no keyword matches)")

    print(f"\n--- SEMANTIC SEARCH ({len(sem)} results) ---")
    for i, r in enumerate(sem, 1):
        name = r["metadata"].get("name", r["id"])
        sim = r["similarity"]
        listeners = r["metadata"].get("listeners", "N/A")
        l_str = f"{int(listeners):,}" if isinstance(listeners, (int, float)) else "N/A"
        print(f"  {i}. {name}  similarity={sim:.4f}  listeners={l_str}")

    return {"keyword": kw, "semantic": sem}
