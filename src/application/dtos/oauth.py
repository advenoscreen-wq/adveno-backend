"""Provider-independent OAuth data transfer objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthTokenResult:
    """Provider-independent OAuth token response."""

    access_token: str
    refresh_token: str | None
    token_type: str
    expires_in: int | None
    scope: str | None = None


@dataclass(frozen=True)
class OAuthUserInfo:
    """Provider-independent authenticated user identity."""

    provider_user_id: str
    email: str | None
    email_verified: bool | None
    name: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True)
class OAuthLoginAttempt:
    """Data stored while an OAuth login is in progress."""

    state: str
    redirect_uri: str
    created_at: float
