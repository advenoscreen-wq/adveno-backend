"""Typed application settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Adveno Backend"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    database_url: str = "postgresql+asyncpg://adveno:adveno_dev_password@localhost:5432/adveno"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: SecretStr = SecretStr("development-only-change-me")
    jwt_issuer: str = "adveno"
    jwt_audience: str = "adveno-api"
    pairing_token_ttl_seconds: int = Field(default=300, ge=1)
    heartbeat_timeout_seconds: int = Field(default=120, ge=1)
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    supabase_url: str = ""
    supabase_anon_key: SecretStr = SecretStr("")
    oauth_provider: str = "google"
    oauth_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/callback"
    oauth_state_ttl_seconds: int = Field(default=600, ge=60)
    session_ttl_seconds: int = Field(default=3600, ge=60)
    session_cookie_name: str = "adveno_session"
    session_cookie_secure: bool = False
    frontend_after_login_url: str = "http://localhost:3000"
    log_level: str = "INFO"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Only allow known deployment environments."""
        normalized = value.lower()
        if normalized not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, or production")
        return normalized

    @field_validator("jwt_secret")
    @classmethod
    def validate_production_secret(cls, value: SecretStr, info: object) -> SecretStr:
        """Reject the local placeholder when production configuration is used."""
        data = getattr(info, "data", {})
        if (
            data.get("environment") == "production"
            and value.get_secret_value() == "development-only-change-me"
        ):
            raise ValueError("JWT_SECRET must be changed in production")
        return value

    @model_validator(mode="after")
    def validate_production_auth(self) -> Settings:
        if self.environment == "production":
            if not self.supabase_url or not self.supabase_anon_key.get_secret_value():
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY are required in production")
            if not self.session_cookie_secure:
                raise ValueError("SESSION_COOKIE_SECURE must be true in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()
