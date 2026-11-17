"""List a user's media assets with optional name filtering and pagination."""

from math import ceil
from uuid import UUID

from application.use_cases.media.results import ListMediaAssetsResult, MediaAssetWithUrl
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.services.storage_service import StorageService


class ListMediaAssetsUseCase:
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

    async def __call__(
        self,
        *,
        user_id: UUID,
        filter_by_name: str | None,
        page: int,
        limit: int,
    ) -> ListMediaAssetsResult:
        name_filter = filter_by_name.strip() if filter_by_name else None
        name_filter = name_filter or None
        total_items = await self._repository.count_by_user_id(
            user_id,
            filter_by_name=name_filter,
        )
        total_pages = ceil(total_items / limit) if total_items else 0
        items = await self._repository.list_by_user_id(
            user_id,
            filter_by_name=name_filter,
            offset=(page - 1) * limit,
            limit=limit,
        )
        return ListMediaAssetsResult(
            items=[
                MediaAssetWithUrl(
                    media=media,
                    media_url=self._storage_service.get_public_url(
                        bucket=self._bucket,
                        object_path=media.storage_path,
                    ),
                )
                for media in items
            ],
            total_pages=total_pages,
            total_items=total_items,
            has_next=page < total_pages,
            has_prev=page > 1,
            limit=limit,
            page=page,
        )
