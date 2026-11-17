"""Request and response schemas for authentication endpoints."""

from pydantic import BaseModel, Field, SecretStr


class RefreshTokenRequest(BaseModel):
    refresh_token: SecretStr = Field(min_length=1)


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int | None
