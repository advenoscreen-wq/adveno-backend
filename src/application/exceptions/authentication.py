"""Authentication application exceptions."""

from application.common.exceptions import AppError


class AuthenticationRequiredError(AppError):
    """Raised when a request has no valid active application user."""

    def __init__(self) -> None:
        super().__init__(
            "Valid authentication is required.",
            code="AUTHENTICATION_REQUIRED",
            status_code=401,
        )


class InvalidAccessTokenError(AppError):
    """Raised when the OAuth provider rejects a bearer access token."""

    def __init__(self) -> None:
        super().__init__(
            "Access token is invalid or expired.",
            code="INVALID_ACCESS_TOKEN",
            status_code=401,
        )
