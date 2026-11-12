"""Typed application settings."""

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
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
    jwt_secret: SecretStr = SecretStr("development-only-change-me")
    jwt_issuer: str = "adveno"
    jwt_audience: str = "adveno-api"
    pairing_token_ttl_seconds: int = Field(default=300, ge=1)
    heartbeat_timeout_seconds: int = Field(default=120, ge=1)
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
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


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()
