"""Record a screen's successfully applied synchronization revision."""

from application.exceptions.screen import ScreenSyncStateNotFoundError, SyncRevisionConflictError
from application.use_cases.screens.commands import AcknowledgeScreenSyncCommand
from application.use_cases.screens.screen_device_auth import authenticate_screen_device
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


class AcknowledgeScreenSyncUseCase:
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

    async def __call__(
        self,
        *,
        credential: str,
        command: AcknowledgeScreenSyncCommand,
    ) -> None:
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
            raise ScreenSyncStateNotFoundError()
        if command.applied_revision > sync_state.desired_revision:
            raise SyncRevisionConflictError()
        if command.applied_revision <= sync_state.applied_revision:
            return

        sync_state.acknowledge_revision(command.applied_revision)
        screen.record_successful_sync()
        await self._sync_state_repository.update(sync_state)
        await self._screen_repository.update(screen)
