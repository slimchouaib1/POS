"""
SVD Collaborative Filtering Engine
───────────────────────────────────
Uses the pre-computed item-item similarity matrix from SVD decomposition
to find items that are mathematically similar to what's in the basket.

This is the "personalized" layer: it captures latent purchase patterns
that FP-Growth might miss (e.g., items that don't co-occur frequently
but appeal to the same customer archetype).

Model Artifacts:
  - svd_item_similarity_matrix.csv  (122 × 122 cosine similarities)
  - svd_model_factors.npz           (U, sigma, Vt, user_means)

Source Notebook: 02_svd_collaborative_filtering.ipynb
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SVDEngine:
    """Item-item collaborative filtering using SVD similarity matrix."""

    def __init__(self):
        self._similarity_matrix: Optional[pd.DataFrame] = None
        self._item_names: list[str] = []
        self._item_name_lower_map: dict[str, str] = {}
        self._loaded = False

    def load(self, base_dir: Path) -> None:
        """Load the pre-computed item similarity matrix."""
        sim_path = base_dir / "data" / "final" / "Module 1" / "svd_item_similarity_matrix.csv"
        if not sim_path.exists():
            logger.warning(f"SVD similarity matrix not found at {sim_path}")
            return

        self._similarity_matrix = pd.read_csv(sim_path, index_col=0)
        self._item_names = list(self._similarity_matrix.columns)
        self._item_name_lower_map = {
            name.lower().strip(): name for name in self._item_names
        }

        logger.info(
            f"[SVD] Loaded {len(self._item_names)}×{len(self._item_names)} "
            f"item similarity matrix"
        )
        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._similarity_matrix is not None

    def _resolve_item_name(self, name: str) -> Optional[str]:
        """Fuzzy-match a basket item name to the similarity matrix column."""
        key = name.lower().strip()
        if key in self._item_name_lower_map:
            return self._item_name_lower_map[key]
        # Try partial match
        for matrix_key, matrix_name in self._item_name_lower_map.items():
            if key in matrix_key or matrix_key in key:
                return matrix_name
        return None

    def recommend(self, basket_items: list[str], top_n: int = 10) -> list[dict]:
        """
        For each item in the basket, look up the most similar items
        from the SVD similarity matrix. Aggregate scores across all
        basket items and return the top-N most similar items.
        """
        if not self.is_loaded:
            return []

        basket_set = {item.lower().strip() for item in basket_items}
        aggregated_scores: dict[str, float] = {}
        matched_sources: dict[str, list[str]] = {}

        for basket_item in basket_items:
            resolved = self._resolve_item_name(basket_item)
            if resolved is None:
                continue

            # Get similarity scores for this item against all others
            similarities = self._similarity_matrix[resolved]

            for item_name, sim_score in similarities.items():
                if item_name.lower().strip() in basket_set:
                    continue  # Skip items already in basket
                if item_name == resolved:
                    continue  # Skip self-similarity

                if sim_score > 0:  # Only positive similarities
                    key = item_name.lower().strip()
                    if key not in aggregated_scores:
                        aggregated_scores[key] = 0.0
                        matched_sources[key] = []
                    aggregated_scores[key] += sim_score
                    matched_sources[key].append(resolved)

        # Sort by aggregated score
        sorted_items = sorted(
            aggregated_scores.items(), key=lambda x: x[1], reverse=True
        )[:top_n]

        results = []
        for item_key, agg_score in sorted_items:
            canonical = self._item_name_lower_map.get(item_key, item_key)
            sources = matched_sources.get(item_key, [])
            source_str = ", ".join(sources[:3])

            results.append({
                "product_name": canonical,
                "score": round(agg_score, 4),
                "confidence": round(min(agg_score * 50, 99), 1),  # Normalize to %
                "lift": round(agg_score, 2),
                "support": 0.0,
                "source_model": "SVD",
                "antecedents": sources[:3],
                "explanation": (
                    f"Similar to items in your basket ({source_str}) "
                    f"based on purchase pattern analysis"
                ),
            })

        logger.debug(f"[SVD] {len(basket_items)} basket items → {len(results)} recommendations")
        return results

    def get_summary(self) -> dict:
        """Return summary stats."""
        if not self.is_loaded:
            return {"total_items": 0, "status": "not_loaded"}

        return {
            "total_items": len(self._item_names),
            "matrix_shape": f"{len(self._item_names)}×{len(self._item_names)}",
            "status": "loaded",
        }
