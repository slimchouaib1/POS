from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

from app.core.deps import get_db, get_current_user, require_role
from app.core.config import settings
from app.ai.anomalies.models import AnomalyAlert, AlertComment
from app.ai.anomalies.service import get_metadata, get_order_details
from app.auth.models import User
from app.audit.models import AuditLog

router = APIRouter(prefix="/api/ai/anomaly", tags=["AI - Anomaly Detection"])


class AlertOut(BaseModel):
    id: int
    order_id: str
    risk_score: float
    risk_level: str
    predicted_label: int
    anomaly_type: str
    reason_codes: str
    alert_explanation: str
    model_name: str
    status: str
    assigned_to: Optional[int]
    assigned_to_name: str = ""
    created_at: Optional[datetime] = None
    comments_count: int = 0

    class Config:
        from_attributes = True


class CommentOut(BaseModel):
    id: int
    alert_id: int
    user_id: Optional[int]
    user_name: str = ""
    comment: str
    action: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertDetailOut(AlertOut):
    comments: list[CommentOut] = Field(default_factory=list)


class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)


AlertStatus = Literal["new", "assigned", "under_review", "confirmed_fraud", "false_positive", "escalated", "closed"]
RiskLevel = Literal["NORMAL", "ALERTE", "CRITIQUE"]


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    status: Optional[AlertStatus] = Query(None),
    risk_level: Optional[RiskLevel] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    q = db.query(AnomalyAlert)
    if status:
        q = q.filter(AnomalyAlert.status == status)
    if risk_level:
        q = q.filter(AnomalyAlert.risk_level == risk_level)
    alerts = q.order_by(AnomalyAlert.risk_score.desc()).limit(limit).all()

    result = []
    for a in alerts:
        user = db.query(User).filter(User.id == a.assigned_to).first() if a.assigned_to else None
        out = AlertOut.model_validate(a)
        out.assigned_to_name = user.full_name if user else ""
        out.comments_count = len(a.comments)
        result.append(out)
    return result


@router.get("/alerts/{alert_id}", response_model=AlertDetailOut)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    alert = db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    user = db.query(User).filter(User.id == alert.assigned_to).first() if alert.assigned_to else None
    out = AlertDetailOut.model_validate(alert)
    out.assigned_to_name = user.full_name if user else ""
    out.comments_count = len(alert.comments)

    comments = []
    for c in alert.comments:
        cu = db.query(User).filter(User.id == c.user_id).first() if c.user_id else None
        co = CommentOut.model_validate(c)
        co.user_name = cu.full_name if cu else "Système"
        comments.append(co)
    out.comments = comments

    return out


@router.patch("/alerts/{alert_id}/status")
def update_alert_status(
    alert_id: int,
    status: AlertStatus = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    alert = db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    old_status = alert.status
    alert.status = status
    if status == "assigned":
        alert.assigned_to = current_user.id

    # Add system comment
    comment = AlertComment(
        alert_id=alert.id,
        user_id=current_user.id,
        comment=f"Statut changé: {old_status} → {status}",
        action="status_change",
    )
    db.add(comment)
    db.add(AuditLog(
        user_id=current_user.id,
        action="update_anomaly_status",
        entity_type="anomaly_alert",
        entity_id=alert.id,
        details=f"Alert {alert.id} status changed from {old_status} to {status}",
    ))
    db.commit()

    return {"detail": "Statut mis à jour", "old_status": old_status, "new_status": status}


@router.post("/alerts/{alert_id}/comment", response_model=CommentOut)
def add_comment(
    alert_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    alert = db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    comment = AlertComment(
        alert_id=alert.id,
        user_id=current_user.id,
        comment=data.comment,
        action="comment",
    )
    db.add(comment)
    db.add(AuditLog(
        user_id=current_user.id,
        action="comment_anomaly",
        entity_type="anomaly_alert",
        entity_id=alert.id,
        details=f"Comment added to alert {alert.id}",
    ))
    db.commit()
    db.refresh(comment)

    out = CommentOut.model_validate(comment)
    out.user_name = current_user.full_name
    return out


@router.get("/metadata")
def anomaly_metadata(_=Depends(get_current_user)):
    return get_metadata()


@router.get("/order-details/{order_id}")
def order_details(
    order_id: str = Path(..., min_length=1, max_length=100),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    """Return full transaction details for an anomaly order from the notebook CSV."""
    details = get_order_details(order_id)
    if not details:
        raise HTTPException(status_code=404, detail="Détails de commande introuvables")
    return details
