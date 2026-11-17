"""Storage service application errors."""

from application.common.exceptions import AppError


class StorageServiceError(AppError):
    """Raised when the configured object storage provider fails."""

    def __init__(self) -> None:
        super().__init__(
            "Object storage request failed.",
            code="STORAGE_SERVICE_ERROR",
            status_code=502,
        )
