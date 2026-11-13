"""Authentication use-case commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleSigninCommand:
    """Request a Google OAuth authorization URL."""

    redirect_uri: str
