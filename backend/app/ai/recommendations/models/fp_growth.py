"""
FP-Growth Association Rule Engine
─────────────────────────────────
Loads pre-mined association rules from the FP-Growth notebook and
matches basket items against antecedent sets to recommend consequent
items with their confidence and lift scores.

Model Artifact: association_rules.csv
Source Notebook: 01_fp_growth.ipynb
"""
import pandas as pd
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FPGrowthEngine:
    """Loads FP-Growth association rules and returns basket-based recommendations."""

    def __init__(self):
        self._rules: Optional[pd.DataFrame] = None
        self._loaded = False

    def load(self, base_dir: Path) -> None:
        """Load association rules from CSV."""
        rules_path = base_dir / "data" / "final" / "Module 1" / "association_rules.csv"
        if not rules_path.exists():
            logger.warning(f"FP-Growth rules not found at {rules_path}")
            return

        self._rules = pd.read_csv(rules_path)

        # The CSV has columns: antecedent, consequent, support, confidence, lift, count
        # antecedent/consequent are single item strings (not frozensets)
        logger.info(
            f"[FP-Growth] Loaded {len(self._rules)} association rules "
            f"(avg confidence: {self._rules['confidence'].mean():.2%}, "
            f"avg lift: {self._rules['lift'].mean():.1f}x)"
        )
        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._rules is not None

    def recommend(self, basket_items: list[str], top_n: int = 10) -> list[dict]:
        """
        Given items currently in the basket, find matching association rules
        where the antecedent is a subset of the basket, and return the
        consequent items ranked by confidence × lift.
        """
        if not self.is_loaded:
            return []

        basket_set = {item.lower().strip() for item in basket_items}
        matches = []

        for _, row in self._rules.iterrows():
            antecedent = str(row.get("antecedent", "")).lower().strip()
            if not antecedent:
                continue

            # Check if the antecedent item is in the basket
            if antecedent in basket_set:
                consequent = str(row.get("consequent", "")).strip()
                if consequent.lower() in basket_set:
                    continue  # Don't recommend items already in basket

                confidence = float(row.get("confidence", 0))
                lift = float(row.get("lift", 1))
                support = float(row.get("support", 0))
                score = confidence * lift

                matches.append({
                    "product_name": consequent,
                    "score": round(score, 4),
                    "confidence": round(confidence * 100, 1),
                    "lift": round(lift, 2),
                    "support": round(support * 100, 2),
                    "source_model": "FP-Growth",
                    "antecedents": [antecedent],
                    "explanation": (
                        f"Customers who buy {antecedent} also buy "
                        f"{consequent} ({confidence*100:.0f}% confidence, "
                        f"{lift:.1f}x lift)"
                    ),
                })

        # Deduplicate: keep the highest score per product
        seen: dict[str, dict] = {}
        for m in sorted(matches, key=lambda x: x["score"], reverse=True):
            key = m["product_name"].lower()
            if key not in seen:
                seen[key] = m

        result = list(seen.values())[:top_n]
        logger.debug(f"[FP-Growth] {len(basket_items)} basket items → {len(result)} recommendations")
        return result

    def get_summary(self) -> dict:
        """Return summary stats about loaded rules."""
        if not self.is_loaded:
            return {"total_rules": 0, "status": "not_loaded"}

        return {
            "total_rules": len(self._rules),
            "avg_confidence": round(self._rules["confidence"].mean() * 100, 1),
            "avg_lift": round(self._rules["lift"].mean(), 2),
            "avg_support": round(self._rules["support"].mean() * 100, 2),
            "status": "loaded",
        }
