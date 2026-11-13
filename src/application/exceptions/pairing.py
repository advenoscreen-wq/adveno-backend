"""Pairing application exceptions."""

from application.common.exceptions import AppError


class PairingSessionNotFoundError(AppError):
    """Raised when a pairing session is missing or its token is invalid."""

    def __init__(self) -> None:
        super().__init__(
            "Pairing session was not found.",
            code="PAIRING_SESSION_NOT_FOUND",
            status_code=404,
        )
