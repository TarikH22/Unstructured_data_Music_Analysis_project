from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """Load the sentence-transformer model once and reuse it."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def build_artist_text(row: pd.Series) -> str:
    """Combine artist fields into a single embeddable text string."""
    parts = []

    name = str(row.get("name", "")).strip()
    if name and name != "nan":
        parts.append(f"Artist: {name}")

    description = str(row.get("description", "")).strip()
    if description and description != "nan":
        parts.append(f"Description: {description}")

    listeners = row.get("listeners", None)
    if pd.notna(listeners):
        try:
            l = int(float(listeners))
            if l > 5_000_000:
                tier = "globally popular"
            elif l > 1_000_000:
                tier = "widely known"
            elif l > 500_000:
                tier = "moderately popular"
            else:
                tier = "emerging"
            parts.append(f"Popularity: {tier} ({l:,} listeners)")
        except (ValueError, TypeError):
            pass

    playcount = row.get("playcount", None)
    if pd.notna(playcount):
        try:
            p = int(float(playcount))
            parts.append(f"Playcount: {p:,} plays")
        except (ValueError, TypeError):
            pass

    source = str(row.get("source_collection", "")).strip()
    if source and source != "nan":
        parts.append(f"Source: {source}")

    return ". ".join(parts) if parts else name


def encode_texts(texts: List[str], batch_size: int = 64, show_progress: bool = False) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Returns an ndarray of shape (len(texts), 384).
    """
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings


def encode_dataframe(df: pd.DataFrame, show_progress: bool = True) -> np.ndarray:
    """Build one text per row and encode the entire DataFrame."""
    texts = [build_artist_text(row) for _, row in df.iterrows()]
    return encode_texts(texts, show_progress=show_progress)
