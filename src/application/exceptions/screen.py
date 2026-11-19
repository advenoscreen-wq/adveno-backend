"""Application errors for screen management operations."""

from application.common.exceptions import AppError


class ScreenNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "The requested screen was not found for this user.",
            code="SCREEN_NOT_FOUND",
            status_code=404,
        )


class ScreenDeviceNotFoundError(AppError):
    """Raised when an authenticated device credential has no screen record."""

    def __init__(self) -> None:
        super().__init__(
            "The screen registered to this device was not found.",
            code="SCREEN_NOT_FOUND",
            status_code=404,
        )


class ScreenDisconnectedError(AppError):
    """Raised when the screen has been disconnected or deactivated."""

    def __init__(self) -> None:
        super().__init__(
            "This screen has been disconnected. Pair it again to continue.",
            code="SCREEN_DISCONNECTED",
            status_code=401,
        )


class InvalidScreenUpdateError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "A valid screen name is required.",
            code="INVALID_SCREEN_UPDATE",
            status_code=422,
        )


class ScreenSyncStateNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Synchronization state was not found for this screen.",
            code="SCREEN_SYNC_STATE_NOT_FOUND",
            status_code=404,
        )


class SyncRevisionConflictError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Applied revision cannot be greater than the screen's desired revision.",
            code="SYNC_REVISION_CONFLICT",
            status_code=409,
        )
