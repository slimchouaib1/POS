from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.recommendations.service import (
    get_frequently_bought_together,
    get_recommendation_summary,
    load_association_rules,
)
from app.audit.models import AuditLog
from app.auth.models import User
from app.core.config import settings
from app.core.deps import get_db, require_role

router = APIRouter(prefix="/api/ai/recommendations", tags=["AI - Recommendations"])


class RecommendationRequest(BaseModel):
    basket_items: list[str] = Field(default_factory=list, max_length=50)
    customer_id: Optional[int] = Field(default=None, gt=0)
    hour: Optional[int] = Field(default=None, ge=0, le=23)
    restaurant_type: str = Field(default="Cafe", max_length=80)
    top_n: int = Field(default=5, ge=1, le=20)


class RecommendationItem(BaseModel):
    product_name: str
    score: float
    confidence: float
    lift: float
    source: list[str]
    explanation: str


@router.post("", response_model=list[RecommendationItem])
def recommend(
    data: RecommendationRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    return get_frequently_bought_together(
        basket_items=data.basket_items,
        customer_id=data.customer_id,
        db=db,
    )


@router.get("/summary")
def rules_summary(_=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER))):
    return get_recommendation_summary()


@router.post("/reload")
def reload_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    load_association_rules()
    db.add(AuditLog(
        user_id=current_user.id,
        action="reload_recommendations",
        entity_type="ai_model",
        details="Recommendation models reloaded",
    ))
    db.commit()
    return {"status": "success", "message": "Recommendation models reloaded successfully."}
