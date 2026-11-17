"""Application errors for playlist operations."""

from application.common.exceptions import AppError


class InvalidPlaylistRequestError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "The playlist details or item ordering are invalid.",
            code="INVALID_PLAYLIST_REQUEST",
            status_code=422,
        )


class PlaylistNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "The requested playlist was not found for this user.",
            code="PLAYLIST_NOT_FOUND",
            status_code=404,
        )
