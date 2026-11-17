"""Authentication use-case commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleSigninCommand:
    """Request a Google OAuth authorization URL."""

    redirect_uri: str


@dataclass(frozen=True)
class GoogleCallbackCommand:
    """Complete Google OAuth using the state and authorization code."""

    code: str
    state: str
    redirect_uri: str


@dataclass(frozen=True)
class RefreshTokenCommand:
    """Refresh a Supabase Auth session using its refresh token."""

    refresh_token: str
