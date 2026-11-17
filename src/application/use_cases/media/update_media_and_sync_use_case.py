"""Update a media record and notify screens using its playlists."""

from uuid import uuid4

from application.exceptions.media import (
    InvalidMediaCreateRequestError,
    MediaAlreadyRegisteredError,
    MediaNotFoundError,
)
from application.use_cases.media.commands import UpdateMediaAndSyncCommand
from application.use_cases.media.results import UpdateMediaAndSyncResult
from domain import MediaAsset
from domain.entities.common import utc_now
from domain.exceptions import PersistenceConflictError
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.repositories.playlist_item_repository import PlaylistItemRepository
from ports.repositories.playlist_repository import PlaylistRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository
from ports.services.storage_service import StorageService


class UpdateMediaAndSyncUseCase:
    def __init__(
        self,
        *,
        media_repository: MediaAssetRepository,
        playlist_item_repository: PlaylistItemRepository,
        playlist_repository: PlaylistRepository,
        assignment_repository: ScreenPlaylistAssignmentRepository,
        sync_state_repository: ScreenSyncStateRepository,
        storage_service: StorageService,
        bucket: str,
    ) -> None:
        self._media_repository = media_repository
        self._playlist_item_repository = playlist_item_repository
        self._playlist_repository = playlist_repository
        self._assignment_repository = assignment_repository
        self._sync_state_repository = sync_state_repository
        self._storage_service = storage_service
        self._bucket = bucket

    async def __call__(self, command: UpdateMediaAndSyncCommand) -> UpdateMediaAndSyncResult:
        current = await self._media_repository.get_by_id(
            command.media_id,
            user_id=command.user_id,
        )
        if current is None:
            raise MediaNotFoundError()

        try:
            if command.is_replaced:
                media = self._replace_media_file(current, command)
            else:
                media = self._rename_media(current, command)
            media = await self._media_repository.update(media)

            playlist_items = await self._playlist_item_repository.list_by_media_asset_id(media.id)
            playlist_ids = list({item.playlist_id for item in playlist_items})
            if command.is_replaced and media.media_type.value == "VIDEO":
                if media.duration_seconds is None:
                    raise InvalidMediaCreateRequestError()
                for playlist_item in playlist_items:
                    playlist_item.update_duration(media.duration_seconds)
                    await self._playlist_item_repository.update(playlist_item)
                await self._playlist_repository.increment_versions(playlist_ids)
            assignments = await self._assignment_repository.list_active_by_playlist_ids(
                playlist_ids
            )
            screen_ids = sorted({assignment.screen_id for assignment in assignments}, key=str)
            sync_states = [
                await self._sync_state_repository.increment_desired_revision(screen_id)
                for screen_id in screen_ids
            ]
        except PersistenceConflictError as error:
            raise MediaAlreadyRegisteredError() from error

        return UpdateMediaAndSyncResult(
            media=media,
            media_url=self._storage_service.get_public_url(
                bucket=self._bucket,
                object_path=media.storage_path,
            ),
            sync_states=sync_states,
        )

    def _replace_media_file(
        self,
        current: MediaAsset,
        command: UpdateMediaAndSyncCommand,
    ) -> MediaAsset:
        if (
            command.media_type is None
            or command.mime_type is None
            or command.storage_path is None
            or command.file_size is None
        ):
            raise InvalidMediaCreateRequestError()
        if command.media_type.value == "VIDEO" and command.duration_seconds is None:
            raise InvalidMediaCreateRequestError()
        storage_path = self._normalize_storage_path(
            command.storage_path,
            user_id=str(command.user_id),
        )
        try:
            return MediaAsset(
                id=current.id,
                user_id=current.user_id,
                name=command.name.strip() if command.name is not None else current.name,
                media_type=command.media_type,
                mime_type=command.mime_type,
                storage_path=storage_path,
                file_size=command.file_size,
                checksum=uuid4().hex,
                width=command.width,
                height=command.height,
                duration_seconds=command.duration_seconds,
                status=current.status,
                created_at=current.created_at,
                updated_at=utc_now(),
            )
        except ValueError as error:
            raise InvalidMediaCreateRequestError() from error

    @staticmethod
    def _rename_media(
        current: MediaAsset,
        command: UpdateMediaAndSyncCommand,
    ) -> MediaAsset:
        if not command.name or not command.name.strip():
            raise InvalidMediaCreateRequestError()
        return MediaAsset(
            id=current.id,
            user_id=current.user_id,
            name=command.name.strip(),
            media_type=current.media_type,
            mime_type=current.mime_type,
            storage_path=current.storage_path,
            file_size=current.file_size,
            checksum=current.checksum,
            width=current.width,
            height=current.height,
            duration_seconds=current.duration_seconds,
            status=current.status,
            created_at=current.created_at,
            updated_at=utc_now(),
        )

    def _normalize_storage_path(self, storage_path: str, *, user_id: str) -> str:
        path = storage_path.strip().strip("/")
        if path.startswith(f"{self._bucket}/"):
            path = path[len(self._bucket) + 1 :]
        segments = path.split("/")
        if (
            len(segments) < 3
            or segments[0] != "users"
            or segments[1] != user_id
            or any(segment in {"", ".", ".."} for segment in segments)
        ):
            raise InvalidMediaCreateRequestError()
        return path
