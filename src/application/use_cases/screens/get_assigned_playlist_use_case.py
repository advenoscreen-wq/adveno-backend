"""Return a screen's assigned playlist with downloadable media details."""

from application.use_cases.screens.results import (
    AssignedPlaylistItem,
    AssignedPlaylistResult,
    PlaylistMediaWithUrl,
)
from application.use_cases.screens.screen_device_auth import authenticate_screen_device
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.repositories.playlist_item_repository import PlaylistItemRepository
from ports.repositories.playlist_repository import PlaylistRepository
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_repository import ScreenRepository
from ports.services.storage_service import StorageService


class GetAssignedPlaylistUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        credential_repository: ScreenCredentialRepository,
        assignment_repository: ScreenPlaylistAssignmentRepository,
        playlist_repository: PlaylistRepository,
        playlist_item_repository: PlaylistItemRepository,
        media_repository: MediaAssetRepository,
        storage_service: StorageService,
        bucket: str,
    ) -> None:
        self._screen_repository = screen_repository
        self._credential_repository = credential_repository
        self._assignment_repository = assignment_repository
        self._playlist_repository = playlist_repository
        self._playlist_item_repository = playlist_item_repository
        self._media_repository = media_repository
        self._storage_service = storage_service
        self._bucket = bucket

    async def __call__(self, *, credential: str) -> AssignedPlaylistResult:
        screen = await authenticate_screen_device(
            credential=credential,
            screen_repository=self._screen_repository,
            credential_repository=self._credential_repository,
        )

        assignment = await self._assignment_repository.get_active_by_screen_id(screen.id)
        if assignment is None:
            return AssignedPlaylistResult(playlist=None, items=[])

        playlist = await self._playlist_repository.get_by_id(
            assignment.playlist_id,
            user_id=screen.user_id,
        )
        if playlist is None:
            return AssignedPlaylistResult(playlist=None, items=[])

        items = await self._playlist_item_repository.list_by_playlist_id(playlist.id)
        playlist_items: list[AssignedPlaylistItem] = []
        for item in items:
            media = await self._media_repository.get_by_id(
                item.media_asset_id,
                user_id=screen.user_id,
            )
            if media is None:
                continue
            playlist_items.append(
                AssignedPlaylistItem(
                    item=item,
                    media=PlaylistMediaWithUrl(
                        media=media,
                        media_url=self._storage_service.get_public_url(
                            bucket=self._bucket,
                            object_path=media.storage_path,
                        ),
                    ),
                )
            )

        return AssignedPlaylistResult(playlist=playlist, items=playlist_items)
