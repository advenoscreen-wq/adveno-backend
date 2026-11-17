"""Delete a playlist and its screen assignment history."""

from uuid import UUID

from application.exceptions.playlist import PlaylistNotFoundError
from ports.repositories.playlist_repository import PlaylistRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


class DeletePlaylistUseCase:
    def __init__(
        self,
        *,
        playlist_repository: PlaylistRepository,
        assignment_repository: ScreenPlaylistAssignmentRepository,
        sync_state_repository: ScreenSyncStateRepository,
    ) -> None:
        self._playlist_repository = playlist_repository
        self._assignment_repository = assignment_repository
        self._sync_state_repository = sync_state_repository

    async def __call__(self, *, playlist_id: UUID, user_id: UUID) -> None:
        playlist = await self._playlist_repository.get_by_id(
            playlist_id,
            user_id=user_id,
        )
        if playlist is None:
            raise PlaylistNotFoundError()

        active_assignments = await self._assignment_repository.list_active_by_playlist_ids(
            [playlist_id]
        )
        screen_ids = sorted({assignment.screen_id for assignment in active_assignments}, key=str)
        for screen_id in screen_ids:
            await self._sync_state_repository.increment_desired_revision(screen_id)

        await self._assignment_repository.delete_by_playlist_id(playlist_id)
        await self._playlist_repository.delete(playlist_id)
