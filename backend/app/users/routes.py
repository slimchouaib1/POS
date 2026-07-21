from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.core.config import settings
from app.auth.models import User
from app.auth.schemas import UserOut, UserUpdate
from app.audit.models import AuditLog

router = APIRouter(prefix="/api/users", tags=["User Management"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN)),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.add(AuditLog(
        user_id=current_user.id,
        action="update_user",
        entity_type="user",
        entity_id=user.id,
        details=f"Updated user {user.username}",
    ))
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_active = False
    db.add(AuditLog(
        user_id=current_user.id,
        action="deactivate_user",
        entity_type="user",
        entity_id=user.id,
        details=f"Deactivated user {user.username}",
    ))
    db.commit()
    return {"detail": "Utilisateur désactivé"}
