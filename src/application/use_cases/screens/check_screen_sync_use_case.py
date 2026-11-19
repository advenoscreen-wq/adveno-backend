"""Record a screen heartbeat and report whether its content is out of date."""

from application.use_cases.screens.results import ScreenSyncCheckResult
from application.use_cases.screens.screen_device_auth import authenticate_screen_device
from domain.value_object import SyncStatus
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

        sync_state = await self._sync_state_repository.get_by_screen_id(
            screen.id,
            for_update=True,
        )
        if sync_state is None:
            sync_state = await self._sync_state_repository.increment_desired_revision(screen.id)
        need_sync = sync_state.desired_revision > sync_state.applied_revision
        if need_sync and sync_state.sync_status is not SyncStatus.SYNCING:
            sync_state.mark_sync_started()
            await self._sync_state_repository.update(sync_state)
        return ScreenSyncCheckResult(
            need_sync=need_sync,
            desired_revision=sync_state.desired_revision,
        )
