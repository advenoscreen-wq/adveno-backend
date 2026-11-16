"""Media application errors."""

from application.common.exceptions import AppError


class InvalidMediaUploadRequestError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "A valid file name is required.",
            code="INVALID_MEDIA_UPLOAD_REQUEST",
            status_code=422,
        )


class InvalidMediaCreateRequestError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "A valid media record and user-owned storage path are required.",
            code="INVALID_MEDIA_CREATE_REQUEST",
            status_code=422,
        )


class MediaAlreadyRegisteredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "This storage object is already registered.",
            code="MEDIA_ALREADY_REGISTERED",
            status_code=409,
        )


class MediaNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "The requested media was not found for this user.",
            code="MEDIA_NOT_FOUND",
            status_code=404,
        )


class MediaScreenNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "The requested screen was not found for this user.",
            code="SCREEN_NOT_FOUND",
            status_code=404,
        )
