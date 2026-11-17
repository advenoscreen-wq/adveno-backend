"""Retrieve a media asset owned by the requesting user."""

from uuid import UUID

from application.exceptions.media import MediaNotFoundError
from application.use_cases.media.results import MediaAssetWithUrl
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.services.storage_service import StorageService


class GetMediaAssetUseCase:
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

    async def __call__(self, *, media_id: UUID, user_id: UUID) -> MediaAssetWithUrl:
        media = await self._repository.get_by_id(media_id, user_id=user_id)
        if media is None:
            raise MediaNotFoundError()
        return MediaAssetWithUrl(
            media=media,
            media_url=self._storage_service.get_public_url(
                bucket=self._bucket,
                object_path=media.storage_path,
            ),
        )
