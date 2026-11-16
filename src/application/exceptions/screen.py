"""Application errors for screen management operations."""

from application.common.exceptions import AppError


class ScreenNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "The requested screen was not found for this user.",
            code="SCREEN_NOT_FOUND",
            status_code=404,
        )


class InvalidScreenUpdateError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "A valid screen name is required.",
            code="INVALID_SCREEN_UPDATE",
            status_code=422,
        )
