from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from app.auth.models import RefreshToken, User
from app.core.config import settings
from app.core.security import (
    create_refresh_token_value,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def create_user(db: Session, username: str, full_name: str, email: str, password: str, role: str = "cashier") -> User:
    user = User(
        username=username,
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_refresh_token(
    db: Session,
    user: User,
    raw_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> RefreshToken:
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=(user_agent or "")[:255] or None,
        ip_address=(ip_address or "")[:64] or None,
    )
    db.add(refresh_token)
    db.flush()
    return refresh_token


def rotate_refresh_token(
    db: Session,
    raw_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[User, str] | None:
    stored_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_refresh_token(raw_token))
        .first()
    )
    now = datetime.utcnow()
    if (
        stored_token is None
        or stored_token.revoked_at is not None
        or stored_token.expires_at <= now
    ):
        return None

    user = db.query(User).filter(User.id == stored_token.user_id).first()
    if user is None or not user.is_active:
        return None

    new_raw_token = create_refresh_token_value()
    new_token = create_refresh_token(db, user, new_raw_token, user_agent, ip_address)
    stored_token.revoked_at = now
    stored_token.replaced_by_token_id = new_token.id
    db.flush()
    return user, new_raw_token


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    stored_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_refresh_token(raw_token))
        .first()
    )
    if stored_token is None or stored_token.revoked_at is not None:
        return False
    stored_token.revoked_at = datetime.utcnow()
    db.flush()
    return True
