"""Permanently delete a screen owned by a user."""

from uuid import UUID

from application.exceptions.screen import ScreenNotFoundError
from ports.repositories.screen_repository import ScreenRepository


class DeleteScreenUseCase:
    def __init__(self, *, screen_repository: ScreenRepository) -> None:
        self._screen_repository = screen_repository

    async def __call__(self, *, screen_id: UUID, user_id: UUID) -> None:
        screen = await self._screen_repository.get_by_id(screen_id, user_id=user_id)
        if screen is None:
            raise ScreenNotFoundError()
        await self._screen_repository.delete(screen_id, user_id=user_id)
