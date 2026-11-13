"""Authentication use-case results."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleSigninResult:
    """Generated provider authorization URL."""

    authorization_url: str
    state: str
