from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import chromadb
from chromadb.config import Settings

from .embedder import build_artist_text, encode_texts

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "embeddings" / "chroma_db"
COLLECTION_NAME = "artists"


def get_client(db_path: Optional[Path] = None) -> chromadb.PersistentClient:
    path = str(db_path or DEFAULT_DB_PATH)
    Path(path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=path)


def get_or_create_collection(
    client: chromadb.PersistentClient,
    name: str = COLLECTION_NAME,
    reset: bool = False,
) -> chromadb.Collection:
    """Return (or reset and recreate) the named collection using cosine similarity."""
    if reset:
        try:
            client.delete_collection(name)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def _safe_metadata(row: pd.Series) -> Dict[str, Any]:
    """Extract scalar metadata fields safe for ChromaDB storage."""
    meta: Dict[str, Any] = {}

    for field in ["name", "source_collection", "url"]:
        val = row.get(field, None)
        if pd.notna(val) and str(val) != "nan":
            meta[field] = str(val)

    for field in ["listeners", "playcount"]:
        val = row.get(field, None)
        if pd.notna(val):
            try:
                meta[field] = int(float(val))
            except (ValueError, TypeError):
                pass

    for field in ["year", "wins", "losses"]:
        val = row.get(field, None)
        if pd.notna(val):
            try:
                meta[field] = int(float(val))
            except (ValueError, TypeError):
                pass

    return meta


def add_artists(
    collection: chromadb.Collection,
    df: pd.DataFrame,
    id_prefix: str = "artist",
    batch_size: int = 64,
    skip_existing: bool = True,
) -> int:
    """Embed and add artist rows to the collection. Returns count added."""
    existing_ids: set = set()
    if skip_existing:
        try:
            existing_ids = set(collection.get(include=[])["ids"])
        except Exception:
            pass

    ids, texts, metadatas = [], [], []
    for idx, (_, row) in enumerate(df.iterrows()):
        doc_id = f"{id_prefix}_{idx}"
        if doc_id in existing_ids:
            continue
        text = build_artist_text(row)
        ids.append(doc_id)
        texts.append(text)
        metadatas.append(_safe_metadata(row))

    if not ids:
        return 0

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i : i + batch_size]
        batch_texts = texts[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]
        embeddings = encode_texts(batch_texts)
        collection.add(
            ids=batch_ids,
            documents=batch_texts,
            embeddings=embeddings.tolist(),
            metadatas=batch_meta,
        )

    return len(ids)


def query_collection(
    collection: chromadb.Collection,
    query_texts: List[str],
    n_results: int = 5,
    where: Optional[Dict] = None,
) -> List[List[Dict]]:
    """Query the collection with one or more query texts.

    Returns a list (one per query) of result lists, each result being a dict
    with keys: id, document, metadata, distance.
    """
    query_embeddings = encode_texts(query_texts)

    kwargs: Dict[str, Any] = {
        "query_embeddings": query_embeddings.tolist(),
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    raw = collection.query(**kwargs)

    results = []
    for q_idx in range(len(query_texts)):
        hits = []
        ids = raw["ids"][q_idx]
        docs = raw["documents"][q_idx]
        metas = raw["metadatas"][q_idx]
        dists = raw["distances"][q_idx]
        for doc_id, doc, meta, dist in zip(ids, docs, metas, dists):
            hits.append({
                "id": doc_id,
                "document": doc,
                "metadata": meta,
                "distance": dist,
                "similarity": 1.0 - dist,
            })
        results.append(hits)

    return results
