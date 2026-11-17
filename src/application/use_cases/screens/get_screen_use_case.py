"""Retrieve a user's screen and its active playlist assignment."""

from uuid import UUID

from application.exceptions.screen import ScreenNotFoundError
from application.use_cases.screens.results import GetScreenResult
from ports.repositories.playlist_repository import PlaylistRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_repository import ScreenRepository


class GetScreenUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        playlist_repository: PlaylistRepository,
        assignment_repository: ScreenPlaylistAssignmentRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._playlist_repository = playlist_repository
        self._assignment_repository = assignment_repository

    async def __call__(self, *, screen_id: UUID, user_id: UUID) -> GetScreenResult:
        screen = await self._screen_repository.get_by_id(screen_id, user_id=user_id)
        if screen is None:
            raise ScreenNotFoundError()

        assignment = await self._assignment_repository.get_active_by_screen_id(screen_id)
        if assignment is None:
            return GetScreenResult(screen=screen, assigned_playlist=None)

        playlist = await self._playlist_repository.get_by_id(
            assignment.playlist_id,
            user_id=user_id,
        )
        return GetScreenResult(screen=screen, assigned_playlist=playlist)
