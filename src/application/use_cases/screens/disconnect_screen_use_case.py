"""Revoke a screen's active device credential without deleting its data."""

from uuid import UUID

from application.exceptions.screen import ScreenNotFoundError
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository


class DisconnectScreenUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        credential_repository: ScreenCredentialRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._credential_repository = credential_repository

    async def __call__(self, *, screen_id: UUID, user_id: UUID) -> None:
        screen = await self._screen_repository.get_by_id(screen_id, user_id=user_id)
        if screen is None:
            raise ScreenNotFoundError()

        credential = await self._credential_repository.get_active_credential_by_screen(
            screen_id,
            for_update=True,
        )
        if credential is None:
            return

        credential.revoke()
        await self._credential_repository.update(credential)
