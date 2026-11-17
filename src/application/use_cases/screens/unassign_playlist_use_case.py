"""Remove a screen's active playlist assignment while preserving its history."""

from uuid import UUID

from application.exceptions.screen import ScreenNotFoundError
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_repository import ScreenRepository
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


class UnassignPlaylistUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        assignment_repository: ScreenPlaylistAssignmentRepository,
        sync_state_repository: ScreenSyncStateRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._assignment_repository = assignment_repository
        self._sync_state_repository = sync_state_repository

    async def __call__(self, *, screen_id: UUID, user_id: UUID) -> None:
        screen = await self._screen_repository.get_by_id(screen_id, user_id=user_id)
        if screen is None:
            raise ScreenNotFoundError()

        assignment = await self._assignment_repository.get_active_by_screen_id(screen_id)
        if assignment is None:
            return

        assignment.unassign()
        await self._assignment_repository.update(assignment)
        await self._sync_state_repository.increment_desired_revision(screen_id)
