from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.deps import get_db, require_role
from app.core.config import settings
from app.audit.models import AuditLog
from app.auth.models import User

router = APIRouter(prefix="/api/audit", tags=["Audit"])


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: str = ""
    action: str
    entity_type: str
    entity_id: Optional[int]
    details: str
    ip_address: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/logs", response_model=list[AuditLogOut])
def list_audit_logs(
    action: Optional[str] = Query(None, max_length=50),
    entity_type: Optional[str] = Query(None, max_length=50),
    user_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    logs = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        out = AuditLogOut.model_validate(log)
        out.user_name = user.full_name if user else "Système"
        result.append(out)
    return result
