"""OAuth application exceptions."""

from application.common.exceptions import AppError


class OAuthProviderError(AppError):
    """Raised when an OAuth provider rejects an operation."""

    def __init__(self, message: str = "OAuth provider request failed") -> None:
        super().__init__(message, code="OAUTH_PROVIDER_ERROR", status_code=502)


class InvalidOAuthStateError(AppError):
    """Raised when an OAuth callback has missing, invalid, or replayed state."""

    def __init__(self, message: str = "OAuth state is invalid or expired") -> None:
        super().__init__(message, code="INVALID_OAUTH_STATE", status_code=400)


class OAuthCallbackError(AppError):
    """Raised when the OAuth provider returns an authorization error."""

    def __init__(self, error: str, error_code: str | None = None) -> None:
        if error_code == "signup_disabled":
            super().__init__(
                "Signups are not allowed for this instance.",
                code="SIGNUP_DISABLED",
                status_code=403,
            )
        elif error == "access_denied":
            super().__init__(
                "OAuth authorization was denied.",
                code="OAUTH_ACCESS_DENIED",
                status_code=400,
            )
        else:
            super().__init__(
                "OAuth authorization could not be completed.",
                code="OAUTH_CALLBACK_ERROR",
                status_code=400,
            )
