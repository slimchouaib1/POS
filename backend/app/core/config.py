from typing import Literal

import hashlib
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # App
    APP_NAME: str = "POS Intelligent Timsoft"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "test", "production"] = "production"
    ENABLE_API_DOCS: bool = False
    SEED_DEMO_DATA: bool = False
    SEED_ADMIN_PASSWORD: str | None = None
    SEED_MANAGER_PASSWORD: str | None = None
    SEED_CASHIER_PASSWORD: str | None = None
    SEED_STOCK_PASSWORD: str | None = None

    # Database
    DATABASE_URL: str = Field(..., min_length=1)

    # JWT
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=5, le=60)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    REFRESH_COOKIE_NAME: str = "pos_refresh_token"
    REFRESH_COOKIE_SECURE: bool = True
    REFRESH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    LOGIN_RATE_LIMIT_ATTEMPTS: int = Field(default=5, ge=1, le=50)
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=300, ge=60, le=3600)

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5175", "http://127.0.0.1:5175"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # Notebooks path (AI data source)
    NOTEBOOKS_PATH: str = str(Path("Ai models"))

    # Roles
    ROLE_ADMIN: str = "admin"
    ROLE_MANAGER: str = "manager"
    ROLE_CASHIER: str = "cashier"
    ROLE_STOCK_MANAGER: str = "stock_manager"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def reject_placeholder_jwt_secret(cls, value: str) -> str:
        weak_values = {
            "change-me",
            "change-me-in-production",
        }
        old_committed_secret_hash = "".join(
            (
                "89915c0b",
                "773e0ab0",
                "a2258c01",
                "ef82e6a4",
                "2e149d96",
                "96795d68",
                "3071734f",
                "732f98a0",
            )
        )
        if (
            value.lower() in weak_values
            or hashlib.sha256(value.encode("utf-8")).hexdigest() == old_committed_secret_hash
        ):
            raise ValueError("JWT_SECRET_KEY must be a strong environment-provided secret")
        return value

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_mode(cls, value):
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in {"release", "production"}:
                return False
            if lowered in {"debug", "development"}:
                return True
        return value

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.CORS_ALLOW_CREDENTIALS and "*" in self.CORS_ORIGINS:
            raise ValueError("Wildcard CORS origins cannot be used when credentials are enabled")
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        if self.REFRESH_COOKIE_SAMESITE == "none" and not self.REFRESH_COOKIE_SECURE:
            raise ValueError("SameSite=None refresh cookies must use Secure")
        return self

    class Config:
        env_file = ".env"


settings = Settings()
