import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user, require_role
from .service import get_forecasts_for_upcoming_week, get_item_forecast, get_ingredient_forecast

router = APIRouter(prefix="/api/ai/forecasting", tags=["AI Forecasting"])
logger = logging.getLogger(__name__)


class ForecastRequest(BaseModel):
    item_name: Optional[str] = Field(default=None, max_length=120)
    section: Optional[str] = Field(default=None, max_length=80)
    horizon_weeks: int = Field(default=8, ge=1, le=52)


@router.get("/next-week", response_model=List[Dict[str, Any]])
def get_next_week_forecast(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "manager", "stock_manager"))
):
    """
    Returns the predicted weekly sales for all menu items,
    along with their current stock levels and status.
    """
    try:
        results = get_forecasts_for_upcoming_week(db)
        return results
    except Exception:
        logger.exception("Error generating forecast")
        raise HTTPException(status_code=500, detail="Forecast generation failed")


@router.post("/predict")
def predict_item_sales(
    req: ForecastRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "manager", "stock_manager"))
):
    """
    Returns predicted weekly sales for a specific item or section,
    including trend, recent average, and per-week breakdown.
    """
    try:
        result = get_item_forecast(db, req.item_name, req.section, req.horizon_weeks)
        return result
    except Exception:
        logger.exception("Error in item forecast")
        raise HTTPException(status_code=500, detail="Forecast generation failed")


@router.get("/ingredient-forecast", response_model=List[Dict[str, Any]])
def ingredient_level_forecast(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "manager", "stock_manager"))
):
    """
    Uses LightGBM menu-item sales predictions + recipe data to compute
    predicted ingredient consumption for next week.
    Compares vs current stock to generate real shortage alerts.
    """
    try:
        results = get_ingredient_forecast(db)
        return results
    except Exception:
        logger.exception("Error in ingredient forecast")
        raise HTTPException(status_code=500, detail="Forecast generation failed")
