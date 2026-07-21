import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.models import User
from app.auth.schemas import LoginRequest, TokenResponse, UserCreate, UserOut
from app.auth.service import (
    authenticate_user,
    create_refresh_token,
    create_user,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.core.config import settings
from app.core.deps import get_current_user, get_db, require_role
from app.core.security import create_access_token, create_refresh_token_value

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

_login_attempts: dict[str, list[float]] = {}


def _rate_limit_key(request: Request, username: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{username.lower()}"


def _check_login_rate_limit(request: Request, username: str) -> None:
    key = _rate_limit_key(request, username)
    now = time.monotonic()
    window_start = now - settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    attempts = [attempt for attempt in _login_attempts.get(key, []) if attempt >= window_start]
    _login_attempts[key] = attempts
    if len(attempts) >= settings.LOGIN_RATE_LIMIT_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )


def _record_failed_login(request: Request, username: str) -> None:
    _login_attempts.setdefault(_rate_limit_key(request, username), []).append(time.monotonic())


def _clear_failed_logins(request: Request, username: str) -> None:
    _login_attempts.pop(_rate_limit_key(request, username), None)


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/api/auth",
    )


@router.post("/login", response_model=TokenResponse)
def login(
    form: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    _check_login_rate_limit(request, form.username)
    user = authenticate_user(db, form.username, form.password)
    if not user:
        _record_failed_login(request, form.username)
        db.add(AuditLog(
            user_id=None,
            action="login_failed",
            entity_type="auth",
            details=f"Failed login attempt for username: {form.username}",
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
        )

    _clear_failed_logins(request, form.username)
    db.add(AuditLog(
        user_id=user.id,
        action="login",
        entity_type="auth",
        details=f"User {user.full_name} logged in",
    ))
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    raw_refresh_token = create_refresh_token_value()
    create_refresh_token(
        db,
        user,
        raw_refresh_token,
        request.headers.get("user-agent"),
        request.client.host if request.client else None,
    )
    db.commit()
    _set_refresh_cookie(response, raw_refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    rotated = rotate_refresh_token(
        db,
        raw_refresh_token,
        request.headers.get("user-agent"),
        request.client.host if request.client else None,
    )
    if rotated is None:
        _clear_refresh_cookie(response)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid")

    user, new_refresh_token = rotated
    db.add(AuditLog(
        user_id=user.id,
        action="refresh_token",
        entity_type="auth",
        details="Refresh token rotated",
    ))
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    db.commit()
    _set_refresh_cookie(response, new_refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if raw_refresh_token:
        revoke_refresh_token(db, raw_refresh_token)
        db.commit()
    _clear_refresh_cookie(response)
    return {"detail": "Logged out"}


@router.post("/register", response_model=UserOut)
def register(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN)),
):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Nom d'utilisateur deja utilise")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email deja utilise")

    user = create_user(db, data.username, data.full_name, data.email, data.password, data.role)
    db.add(AuditLog(
        user_id=current_user.id,
        action="create_user",
        entity_type="user",
        entity_id=user.id,
        details=f"Created user {user.full_name} with role {user.role}",
    ))
    db.commit()
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
