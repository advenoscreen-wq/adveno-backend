"""Update user-managed screen details."""

from uuid import UUID

from application.exceptions.screen import InvalidScreenUpdateError, ScreenNotFoundError
from domain import Screen
from domain.exceptions import DomainError
from ports.repositories.screen_repository import ScreenRepository


class UpdateScreenUseCase:
    def __init__(self, *, repository: ScreenRepository) -> None:
        self._repository = repository

    async def __call__(self, *, screen_id: UUID, user_id: UUID, name: str) -> Screen:
        screen = await self._repository.get_by_id(screen_id, user_id=user_id)
        if screen is None:
            raise ScreenNotFoundError()
        try:
            screen.rename(name)
        except DomainError as error:
            raise InvalidScreenUpdateError() from error
        return await self._repository.update(screen)
