"""Record a screen heartbeat and report whether its content is out of date."""

import hashlib

from application.exceptions.authentication import InvalidScreenCredentialError
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


class CheckScreenSyncUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        credential_repository: ScreenCredentialRepository,
        sync_state_repository: ScreenSyncStateRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._credential_repository = credential_repository
        self._sync_state_repository = sync_state_repository

    async def __call__(self, *, credential: str) -> bool:
        credential_hash = hashlib.sha256(credential.encode("utf-8")).hexdigest()
        device_credential = await self._credential_repository.get_active_by_hash(credential_hash)
        if device_credential is None:
            raise InvalidScreenCredentialError()

        screen = await self._screen_repository.get_by_id(device_credential.screen_id)
        if screen is None or not device_credential.is_valid(screen_active=screen.is_active):
            raise InvalidScreenCredentialError()

        device_credential.mark_as_used()
        screen.record_heartbeat()
        await self._credential_repository.update(device_credential)
        await self._screen_repository.update(screen)

        sync_state = await self._sync_state_repository.get_by_screen_id(screen.id)
        return sync_state is None or sync_state.desired_revision > sync_state.applied_revision
