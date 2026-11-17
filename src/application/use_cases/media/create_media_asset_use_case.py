"""Register metadata for an uploaded media object."""

from uuid import uuid4

from application.exceptions.media import (
    InvalidMediaCreateRequestError,
    MediaAlreadyRegisteredError,
)
from application.use_cases.media.commands import CreateMediaAssetCommand
from application.use_cases.media.results import CreateMediaAssetResult
from domain import MediaAsset
from domain.exceptions import PersistenceConflictError
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.services.storage_service import StorageService


class CreateMediaAssetUseCase:
    def __init__(
        self,
        *,
        repository: MediaAssetRepository,
        storage_service: StorageService,
        bucket: str,
    ) -> None:
        self._repository = repository
        self._storage_service = storage_service
        self._bucket = bucket

    async def __call__(self, command: CreateMediaAssetCommand) -> CreateMediaAssetResult:
        storage_path = self._normalize_storage_path(
            command.storage_path,
            user_id=str(command.user_id),
        )
        try:
            media = MediaAsset(
                user_id=command.user_id,
                name=command.name,
                media_type=command.media_type,
                mime_type=command.mime_type,
                storage_path=storage_path,
                file_size=command.file_size,
                checksum=uuid4().hex,
                width=command.width,
                height=command.height,
                duration_seconds=command.duration_seconds,
            )
        except ValueError as error:
            raise InvalidMediaCreateRequestError() from error

        try:
            media = await self._repository.save(media)
        except PersistenceConflictError as error:
            raise MediaAlreadyRegisteredError() from error
        return CreateMediaAssetResult(
            media=media,
            media_url=self._storage_service.get_public_url(
                bucket=self._bucket,
                object_path=media.storage_path,
            ),
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
