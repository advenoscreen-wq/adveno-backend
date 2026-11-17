"""Assign a playlist to a user's screen."""

from uuid import UUID

from application.exceptions.playlist import PlaylistNotFoundError
from application.exceptions.screen import ScreenNotFoundError
from domain import ScreenPlaylistAssignment
from ports.repositories.playlist_repository import PlaylistRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_repository import ScreenRepository
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


class AssignPlaylistUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        playlist_repository: PlaylistRepository,
        assignment_repository: ScreenPlaylistAssignmentRepository,
        sync_state_repository: ScreenSyncStateRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._playlist_repository = playlist_repository
        self._assignment_repository = assignment_repository
        self._sync_state_repository = sync_state_repository

    async def __call__(
        self, *, screen_id: UUID, playlist_id: UUID, user_id: UUID
    ) -> ScreenPlaylistAssignment:
        screen = await self._screen_repository.get_by_id(screen_id, user_id=user_id)
        if screen is None:
            raise ScreenNotFoundError()
        playlist = await self._playlist_repository.get_by_id(playlist_id, user_id=user_id)
        if playlist is None:
            raise PlaylistNotFoundError()

        current_assignment = await self._assignment_repository.get_active_by_screen_id(screen_id)
        if current_assignment is not None and current_assignment.playlist_id == playlist_id:
            return current_assignment

        if current_assignment is not None:
            current_assignment.unassign()
            await self._assignment_repository.update(current_assignment)

        assignment = await self._assignment_repository.save(
            ScreenPlaylistAssignment(screen_id=screen_id, playlist_id=playlist_id)
        )
        await self._sync_state_repository.increment_desired_revision(screen_id)
        return assignment
