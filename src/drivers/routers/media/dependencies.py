"""Dependencies for media routes."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.media_asset_repository import SqlAlchemyMediaAssetRepository
from adapters.repositories.playlist_item_repository import SqlAlchemyPlaylistItemRepository
from adapters.repositories.screen_playlist_assignment_repository import (
    SqlAlchemyScreenPlaylistAssignmentRepository,
)
from adapters.repositories.screen_sync_state_repository import (
    SqlAlchemyScreenSyncStateRepository,
)
from adapters.services.storage.supabase_storage_service import SupabaseStorageService
from application.use_cases.media.create_media_asset_use_case import CreateMediaAssetUseCase
from application.use_cases.media.get_media_asset_use_case import GetMediaAssetUseCase
from application.use_cases.media.list_media_assets_use_case import ListMediaAssetsUseCase
from application.use_cases.media.request_media_replacement_upload_url_use_case import (
    RequestMediaReplacementUploadUrlUseCase,
)
from application.use_cases.media.request_media_upload_url_use_case import (
    RequestMediaUploadUrlUseCase,
)
from application.use_cases.media.update_media_and_sync_use_case import (
    UpdateMediaAndSyncUseCase,
)
from drivers.database.database import session_dependency
from drivers.routers.dependencies import SettingsDependency
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.repositories.playlist_item_repository import PlaylistItemRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository
from ports.services.storage_service import StorageService


@lru_cache(maxsize=8)
def _storage_service(supabase_url: str, anon_key: str) -> SupabaseStorageService:
    return SupabaseStorageService(
        supabase_url=supabase_url,
        supabase_anon_key=anon_key,
    )


def get_storage_service(settings: SettingsDependency) -> StorageService:
    """Build the Supabase Storage adapter from application settings."""
    return _storage_service(
        settings.supabase_url,
        settings.supabase_anon_key.get_secret_value(),
    )


StorageServiceDependency = Annotated[
    StorageService,
    Depends(get_storage_service),
]


def get_request_media_upload_url_use_case(
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> RequestMediaUploadUrlUseCase:
    """Build the media upload URL use case."""
    return RequestMediaUploadUrlUseCase(
        storage_service=storage_service,
        bucket=settings.media_storage_bucket,
    )


RequestMediaUploadUrl = Annotated[
    RequestMediaUploadUrlUseCase,
    Depends(get_request_media_upload_url_use_case),
]


def get_media_asset_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> MediaAssetRepository:
    """Build the request-scoped media asset repository."""
    return SqlAlchemyMediaAssetRepository(session)


MediaAssetRepositoryDependency = Annotated[
    MediaAssetRepository,
    Depends(get_media_asset_repository),
]


def get_media_asset_use_case(
    repository: MediaAssetRepositoryDependency,
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> GetMediaAssetUseCase:
    """Build the media asset lookup use case."""
    return GetMediaAssetUseCase(
        repository=repository,
        storage_service=storage_service,
        bucket=settings.media_storage_bucket,
    )


GetMediaAsset = Annotated[
    GetMediaAssetUseCase,
    Depends(get_media_asset_use_case),
]


def get_list_media_assets_use_case(
    repository: MediaAssetRepositoryDependency,
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> ListMediaAssetsUseCase:
    """Build the paginated media listing use case."""
    return ListMediaAssetsUseCase(
        repository=repository,
        storage_service=storage_service,
        bucket=settings.media_storage_bucket,
    )


ListMediaAssets = Annotated[
    ListMediaAssetsUseCase,
    Depends(get_list_media_assets_use_case),
]


def get_request_media_replacement_upload_url_use_case(
    media_repository: MediaAssetRepositoryDependency,
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> RequestMediaReplacementUploadUrlUseCase:
    """Build the media replacement upload URL use case."""
    return RequestMediaReplacementUploadUrlUseCase(
        media_repository=media_repository,
        storage_service=storage_service,
        bucket=settings.media_storage_bucket,
    )


RequestMediaReplacementUploadUrl = Annotated[
    RequestMediaReplacementUploadUrlUseCase,
    Depends(get_request_media_replacement_upload_url_use_case),
]


def get_create_media_asset_use_case(
    repository: MediaAssetRepositoryDependency,
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> CreateMediaAssetUseCase:
    """Build the media record creation use case."""
    return CreateMediaAssetUseCase(
        repository=repository,
        storage_service=storage_service,
        bucket=settings.media_storage_bucket,
    )


CreateMediaAsset = Annotated[
    CreateMediaAssetUseCase,
    Depends(get_create_media_asset_use_case),
]


def get_playlist_item_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> PlaylistItemRepository:
    """Build the request-scoped playlist item repository."""
    return SqlAlchemyPlaylistItemRepository(session)


def get_screen_playlist_assignment_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenPlaylistAssignmentRepository:
    """Build the request-scoped screen playlist assignment repository."""
    return SqlAlchemyScreenPlaylistAssignmentRepository(session)


def get_screen_sync_state_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenSyncStateRepository:
    """Build the request-scoped synchronization state repository."""
    return SqlAlchemyScreenSyncStateRepository(session)


def get_update_media_and_sync_use_case(
    media_repository: MediaAssetRepositoryDependency,
    playlist_item_repository: Annotated[
        PlaylistItemRepository,
        Depends(get_playlist_item_repository),
    ],
    assignment_repository: Annotated[
        ScreenPlaylistAssignmentRepository,
        Depends(get_screen_playlist_assignment_repository),
    ],
    sync_state_repository: Annotated[
        ScreenSyncStateRepository,
        Depends(get_screen_sync_state_repository),
    ],
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> UpdateMediaAndSyncUseCase:
    """Build the use case that updates media and bumps screen sync revision."""
    return UpdateMediaAndSyncUseCase(
        media_repository=media_repository,
        playlist_item_repository=playlist_item_repository,
        assignment_repository=assignment_repository,
        sync_state_repository=sync_state_repository,
        storage_service=storage_service,
        bucket=settings.media_storage_bucket,
    )


UpdateMediaAndSync = Annotated[
    UpdateMediaAndSyncUseCase,
    Depends(get_update_media_and_sync_use_case),
]
