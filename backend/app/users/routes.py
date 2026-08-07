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
    old_role = user.role
    was_active = user.is_active
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(user, k, v)
    if "role" in updates and updates["role"] != old_role:
        db.add(AuditLog(
            user_id=current_user.id,
            action="user_role_changed",
            entity_type="user",
            entity_id=user.id,
            details=f"Changed user {user.username} role from {old_role} to {user.role}",
        ))
    if "is_active" in updates and was_active and user.is_active is False:
        db.add(AuditLog(
            user_id=current_user.id,
            action="user_deactivated",
            entity_type="user",
            entity_id=user.id,
            details=f"Deactivated user {user.username}",
        ))
    other_fields = sorted(set(updates) - {"role", "is_active"})
    if other_fields or not updates:
        db.add(AuditLog(
            user_id=current_user.id,
            action="user_updated",
            entity_type="user",
            entity_id=user.id,
            details=f"Updated user {user.username}; fields={','.join(other_fields) if other_fields else 'none'}",
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
        action="user_deactivated",
        entity_type="user",
        entity_id=user.id,
        details=f"Deactivated user {user.username}",
    ))
    db.commit()
    return {"detail": "Utilisateur désactivé"}
