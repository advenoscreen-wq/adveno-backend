"""Revoke the authenticated screen's device credential."""

from application.use_cases.screens.screen_device_auth import (
    authenticate_screen_device_with_credential,
)
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository


class LogoutScreenUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        credential_repository: ScreenCredentialRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._credential_repository = credential_repository

    async def __call__(self, *, credential: str) -> None:
        _, device_credential = await authenticate_screen_device_with_credential(
            credential=credential,
            screen_repository=self._screen_repository,
            credential_repository=self._credential_repository,
            persist_credential=False,
        )
        device_credential.revoke()
        await self._credential_repository.update(device_credential)
