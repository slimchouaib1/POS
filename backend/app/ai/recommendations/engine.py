"""
Hybrid Recommendation Engine Orchestrator
─────────────────────────────────────────
Blends scores from:
 1. FP-Growth (Frequent item associations based on basket)
 2. SVD (Collaborative filtering similarity based on basket)
 3. FM (Context-aware re-ranking based on time/day/restaurant)

This is the main entry point for the recommendations API.
"""
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from .models.fp_growth import FPGrowthEngine
from .models.svd_cf import SVDEngine
from .models.fm_context import FMEngine

logger = logging.getLogger(__name__)


class RecommendationResult(BaseModel):
    product_name: str
    final_score: float
    fp_growth_score: float = 0.0
    svd_score: float = 0.0
    fm_multiplier: float = 1.0
    confidence: float = 0.0
    lift: float = 0.0
    source_models: list[str] = []
    explanation: str


class HybridEngine:
    def __init__(self):
        self.fp_growth = FPGrowthEngine()
        self.svd = SVDEngine()
        self.fm = FMEngine()
        self._loaded = False

    def load_all(self, base_model_dir: Path) -> None:
        """Load all three models from disk."""
        logger.info(f"Loading AI Recommendation Models from {base_model_dir}...")
        try:
            self.fp_growth.load(base_model_dir)
            self.svd.load(base_model_dir)
            self.fm.load(base_model_dir)
            self._loaded = True
            logger.info("All AI Recommendation Models loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load AI recommendation models: {e}")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_summary(self) -> dict:
        return {
            "fp_growth": self.fp_growth.get_summary(),
            "svd": self.svd.get_summary(),
            "fm": self.fm.get_summary(),
            "status": "loaded" if self._loaded else "not_loaded"
        }

    def recommend(
        self,
        basket_items: list[str],
        customer_history: Optional[list[str]] = None,
        hour: Optional[int] = None,
        restaurant_type: str = "Cafe",
        top_n: int = 5
    ) -> list[RecommendationResult]:
        """
        Get hybrid recommendations for a given basket and context.
        If customer_history has >= 5 items, activate the SVD personalized layer.
        """
        if not self._loaded:
            logger.warning("HybridEngine not loaded. Returning empty recommendations.")
            return []

        # 1. Get base recommendations from FP-Growth and SVD
        fp_recs = self.fp_growth.recommend(basket_items, top_n=20)
        
        # Cold-start guard: only run SVD if we have sufficient customer history
        if customer_history and len(set(customer_history)) >= 5:
            # Combine current basket with past history to find similar items
            combined_items = list(set(basket_items + customer_history))
            svd_recs = self.svd.recommend(combined_items, top_n=20)
            logger.debug(f"SVD enabled. customer_history size: {len(set(customer_history))}")
        else:
            svd_recs = []
            logger.debug("SVD disabled (cold-start or no customer).")

        # Merge results keyed by lowercase item name
        merged: dict[str, dict] = {}

        for rec in fp_recs:
            key = rec["product_name"].lower().strip()
            merged[key] = {
                "product_name": rec["product_name"],
                "fp_score": rec["score"],
                "svd_score": 0.0,
                "confidence": rec["confidence"],
                "lift": rec["lift"],
                "sources": ["FP-Growth"],
                "explanation_parts": [rec["explanation"]]
            }

        for rec in svd_recs:
            key = rec["product_name"].lower().strip()
            if key in merged:
                merged[key]["svd_score"] = rec["score"]
                merged[key]["sources"].append("SVD")
                # Combine explanations gracefully
                merged[key]["explanation_parts"].append("Also mathematically similar to other items in your cart.")
            else:
                merged[key] = {
                    "product_name": rec["product_name"],
                    "fp_score": 0.0,
                    "svd_score": rec["score"],
                    "confidence": rec["confidence"],
                    "lift": rec["lift"],
                    "sources": ["SVD"],
                    "explanation_parts": [rec["explanation"]]
                }

        if not merged:
            # If basket is empty or no matches, return FM general recommendations
            fm_general = self.fm.score_items(hour=hour, restaurant_type=restaurant_type)[:top_n]
            return [
                RecommendationResult(
                    product_name=rec["item_name"],
                    final_score=rec["score"],
                    fm_multiplier=rec["score"],
                    source_models=["FM"],
                    explanation="Recommended for this time of day based on historical trends."
                )
                for rec in fm_general
            ]

        # 2. Get FM Context Multipliers for the candidates
        candidates = list(merged.keys())
        fm_multipliers = self.fm.get_context_multipliers(candidates, hour=hour)

        # 3. Calculate Final Blended Score
        # Strategy: (Normalized FP Score + Normalized SVD Score) * FM Context Multiplier
        
        # Normalize FP scores (max = 1.0)
        max_fp = max([m["fp_score"] for m in merged.values()] + [0.001])
        # Normalize SVD scores (max = 1.0)
        max_svd = max([m["svd_score"] for m in merged.values()] + [0.001])

        results = []
        for key, data in merged.items():
            norm_fp = data["fp_score"] / max_fp
            norm_svd = data["svd_score"] / max_svd
            
            # Base blend: 60% FP-Growth (explicit rules) + 40% SVD (latent patterns)
            base_score = (0.6 * norm_fp) + (0.4 * norm_svd)
            
            # Apply Context Multiplier
            multiplier = fm_multipliers.get(key, 1.0)
            final_score = base_score * multiplier
            
            # Add FM to sources if it modulated the score at all
            sources = data["sources"]
            if multiplier != 1.0:
                sources.append("FM Context")
                if multiplier > 1.2:
                    data["explanation_parts"].append("Highly popular at this time of day.")

            # Compile explanation
            explanation = " ".join(data["explanation_parts"])

            results.append(RecommendationResult(
                product_name=data["product_name"],
                final_score=round(final_score, 4),
                fp_growth_score=round(data["fp_score"], 4),
                svd_score=round(data["svd_score"], 4),
                fm_multiplier=round(multiplier, 2),
                confidence=data["confidence"],
                lift=data["lift"],
                source_models=sources,
                explanation=explanation
            ))

        # 4. Sort by final score and return top N
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:top_n]
