"""Application exceptions."""

from application.common.exceptions import AppError, ApplicationError
from application.exceptions.oauth import (
    InvalidOAuthStateError,
    OAuthCallbackError,
    OAuthProviderError,
)

__all__ = [
    "AppError",
    "ApplicationError",
    "InvalidOAuthStateError",
    "OAuthCallbackError",
    "OAuthProviderError",
]
