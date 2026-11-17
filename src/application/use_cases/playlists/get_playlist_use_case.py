"""Retrieve a playlist owned by a user."""

from uuid import UUID

from application.exceptions.playlist import PlaylistNotFoundError
from domain import Playlist
from ports.repositories.playlist_repository import PlaylistRepository


class GetPlaylistUseCase:
    def __init__(self, *, playlist_repository: PlaylistRepository) -> None:
        self._playlist_repository = playlist_repository

    async def __call__(self, *, playlist_id: UUID, user_id: UUID) -> Playlist:
        playlist = await self._playlist_repository.get_by_id(
            playlist_id,
            user_id=user_id,
        )
        if playlist is None:
            raise PlaylistNotFoundError()
        return playlist
