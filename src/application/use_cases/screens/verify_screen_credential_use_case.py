"""Verify that a TV's stored screen credential is still active."""

from application.use_cases.screens.screen_device_auth import authenticate_screen_device
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository


class VerifyScreenCredentialUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        credential_repository: ScreenCredentialRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._credential_repository = credential_repository

    async def __call__(self, *, credential: str) -> None:
        await authenticate_screen_device(
            credential=credential,
            screen_repository=self._screen_repository,
            credential_repository=self._credential_repository,
        )
