"""Create an overwrite-enabled upload URL for an owned media object."""

from application.exceptions.media import MediaNotFoundError
from application.use_cases.media.commands import (
    RequestMediaReplacementUploadUrlCommand,
)
from application.use_cases.media.results import (
    RequestMediaReplacementUploadUrlResult,
)
from domain.value_object import MediaStatus
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.services.storage_service import StorageService


class RequestMediaReplacementUploadUrlUseCase:
    def __init__(
        self,
        *,
        media_repository: MediaAssetRepository,
        storage_service: StorageService,
        bucket: str,
    ) -> None:
        self._media_repository = media_repository
        self._storage_service = storage_service
        self._bucket = bucket

    async def __call__(
        self,
        command: RequestMediaReplacementUploadUrlCommand,
    ) -> RequestMediaReplacementUploadUrlResult:
        media = await self._media_repository.get_by_id(
            command.media_id,
            user_id=command.user_id,
        )
        if media is None or media.status is not MediaStatus.ACTIVE:
            raise MediaNotFoundError()

        signed_url = await self._storage_service.create_signed_upload_url(
            bucket=self._bucket,
            object_path=media.storage_path,
            access_token=command.access_token,
            upsert=True,
        )
        return RequestMediaReplacementUploadUrlResult(
            signed_url=signed_url,
            storage_path=media.storage_path,
        )
