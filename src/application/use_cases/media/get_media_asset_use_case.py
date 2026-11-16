"""Retrieve a media asset owned by the requesting user."""

from uuid import UUID

from application.exceptions.media import MediaNotFoundError
from domain import MediaAsset
from ports.repositories.media_asset_repository import MediaAssetRepository


class GetMediaAssetUseCase:
    def __init__(self, *, repository: MediaAssetRepository) -> None:
        self._repository = repository

    async def __call__(self, *, media_id: UUID, user_id: UUID) -> MediaAsset:
        media = await self._repository.get_by_id(media_id, user_id=user_id)
        if media is None:
            raise MediaNotFoundError()
        return media
