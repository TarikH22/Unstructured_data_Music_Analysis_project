from __future__ import annotations

from typing import Dict

import numpy as np


def _array_metadata(arr: np.ndarray) -> Dict[str, object]:
    """Return key ndarray attributes for quick inspection."""
    return {
        "dtype": str(arr.dtype),
        "shape": arr.shape,
        "ndim": arr.ndim,
        "size": arr.size,
        "itemsize": arr.itemsize,
    }


def create_numpy_arrays() -> Dict[str, np.ndarray]:
    """Create movie-oriented arrays using 4+ NumPy creation methods."""
    return {
        "ratings_array": np.array([7.2, 8.1, 6.9, 7.8, 8.7, 5.4], dtype=np.float64),
        "popularity_arange": np.arange(10, 70, 10, dtype=np.int32),
        "timeline_linspace": np.linspace(0, 1, 6, dtype=np.float64),
        "budget_zeros": np.zeros(6, dtype=np.int64),
        "vote_count_ones": np.ones(6, dtype=np.int64),
        "genre_matrix": np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int16),
    }


def vectorized_movie_metrics(
    ratings: np.ndarray,
    popularity: np.ndarray,
    vote_count: np.ndarray,
) -> Dict[str, np.ndarray]:
    """Run vectorized arithmetic with no Python loops."""
    ratings = ratings.astype(np.float64)
    popularity = popularity.astype(np.float64)
    vote_count = vote_count.astype(np.float64)

    pop_norm = (popularity - popularity.min()) / (popularity.ptp() + 1e-12)
    votes_norm = np.log1p(vote_count)

    weighted_score = (ratings * 0.7) + (pop_norm * 0.2) + (votes_norm * 0.1)
    centered_ratings = ratings - ratings.mean()
    z_scores = centered_ratings / (ratings.std(ddof=0) + 1e-12)

    return {
        "popularity_normalized": pop_norm,
        "weighted_score": weighted_score,
        "ratings_centered": centered_ratings,
        "ratings_z_score": z_scores,
    }


def run_numpy_foundations() -> Dict[str, object]:
    """Execute NumPy foundation tasks and return structured results."""
    arrays = create_numpy_arrays()

    metrics = vectorized_movie_metrics(
        ratings=arrays["ratings_array"],
        popularity=arrays["popularity_arange"],
        vote_count=np.array([120, 620, 340, 890, 1400, 90], dtype=np.int64),
    )

    stats = {
        "ratings_mean": float(np.mean(arrays["ratings_array"])),
        "ratings_std": float(np.std(arrays["ratings_array"])),
        "ratings_min": float(np.min(arrays["ratings_array"])),
        "ratings_max": float(np.max(arrays["ratings_array"])),
    }

    metadata = {name: _array_metadata(arr) for name, arr in arrays.items()}

    return {
        "arrays": arrays,
        "array_metadata": metadata,
        "vectorized_metrics": metrics,
        "statistics": stats,
    }
