"""Record a screen heartbeat and report whether its content is out of date."""

from application.use_cases.screens.results import ScreenSyncCheckResult
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

    async def __call__(self, *, credential: str) -> ScreenSyncCheckResult:
        screen = await authenticate_screen_device(
            credential=credential,
            screen_repository=self._screen_repository,
            credential_repository=self._credential_repository,
        )

        sync_state = await self._sync_state_repository.get_by_screen_id(screen.id)
        if sync_state is None:
            sync_state = await self._sync_state_repository.increment_desired_revision(screen.id)
        return ScreenSyncCheckResult(
            need_sync=sync_state.desired_revision > sync_state.applied_revision,
            desired_revision=sync_state.desired_revision,
        )
