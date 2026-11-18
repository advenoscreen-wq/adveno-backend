"""Record a screen heartbeat and report whether its content is out of date."""

from application.use_cases.screens.screen_device_auth import authenticate_screen_device
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
        screen = await authenticate_screen_device(
            credential=credential,
            screen_repository=self._screen_repository,
            credential_repository=self._credential_repository,
        )

        sync_state = await self._sync_state_repository.get_by_screen_id(screen.id)
        return sync_state is None or sync_state.desired_revision > sync_state.applied_revision
