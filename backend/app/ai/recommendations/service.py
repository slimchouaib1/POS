import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from .engine import HybridEngine

logger = logging.getLogger(__name__)

# Global instance of the hybrid engine
hybrid_engine = HybridEngine()

def load_association_rules(model_path: str = "Ai models") -> None:
    """
    Called at app startup to load the recommendation models into memory.
    The path is relative to the backend root (e.g., 'Ai models/Module 1').
    """
    try:
        base_dir = Path(model_path)
        hybrid_engine.load_all(base_dir)
        logger.info("Hybrid Recommendation engine initialization complete.")
    except Exception as e:
        logger.error(f"Failed to load Hybrid Recommendation engine: {e}")

def get_frequently_bought_together(
    basket_items: list[str],
    customer_id: Optional[int] = None,
    db: Optional[Session] = None
) -> list[dict]:
    """
    Returns hybrid recommendations for the current basket.
    Conditionally runs personalization if customer_id is provided and has enough history.
    """
    customer_history = []
    
    if customer_id is not None and db is not None:
        try:
            # Fetch distinct products previously purchased by this customer
            query = text("""
                SELECT DISTINCT oi.product_name 
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                WHERE o.customer_id = :customer_id AND o.status = 'paid'
            """)
            result = db.execute(query, {"customer_id": customer_id}).fetchall()
            customer_history = [row[0] for row in result]
            logger.debug(f"Fetched {len(customer_history)} distinct past items for customer {customer_id}")
        except Exception as e:
            logger.error(f"Error fetching customer history for recommendations: {e}")

    # For now we use default context (current time, "Cafe" restaurant)
    results = hybrid_engine.recommend(
        basket_items=basket_items,
        customer_history=customer_history,
        top_n=5
    )
    
    return [
        {
            "product_name": r.product_name,
            "confidence": r.confidence,
            "lift": r.lift,
            "score": r.final_score,
            "explanation": r.explanation,
            "source": r.source_models
        }
        for r in results
    ]

def get_recommendation_summary() -> dict:
    """
    Returns statistics about the loaded models.
    """
    return hybrid_engine.get_summary()
