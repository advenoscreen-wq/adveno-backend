"""Dependencies for playlist management routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.media_asset_repository import SqlAlchemyMediaAssetRepository
from adapters.repositories.playlist_item_repository import SqlAlchemyPlaylistItemRepository
from adapters.repositories.playlist_repository import SqlAlchemyPlaylistRepository
from adapters.repositories.screen_playlist_assignment_repository import (
    SqlAlchemyScreenPlaylistAssignmentRepository,
)
from adapters.repositories.screen_sync_state_repository import SqlAlchemyScreenSyncStateRepository
from application.use_cases.playlists.create_playlist_use_case import CreatePlaylistUseCase
from application.use_cases.playlists.delete_playlist_use_case import DeletePlaylistUseCase
from application.use_cases.playlists.get_playlist_use_case import GetPlaylistUseCase
from application.use_cases.playlists.list_playlists_use_case import ListPlaylistsUseCase
from application.use_cases.playlists.update_playlist_use_case import UpdatePlaylistUseCase
from drivers.database.database import session_dependency
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.repositories.playlist_item_repository import PlaylistItemRepository
from ports.repositories.playlist_repository import PlaylistRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


def get_playlist_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> PlaylistRepository:
    return SqlAlchemyPlaylistRepository(session)


def get_playlist_item_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> PlaylistItemRepository:
    return SqlAlchemyPlaylistItemRepository(session)


def get_media_asset_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> MediaAssetRepository:
    return SqlAlchemyMediaAssetRepository(session)


def get_screen_playlist_assignment_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenPlaylistAssignmentRepository:
    return SqlAlchemyScreenPlaylistAssignmentRepository(session)


def get_screen_sync_state_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenSyncStateRepository:
    return SqlAlchemyScreenSyncStateRepository(session)


PlaylistRepositoryDependency = Annotated[
    PlaylistRepository,
    Depends(get_playlist_repository),
]
PlaylistItemRepositoryDependency = Annotated[
    PlaylistItemRepository,
    Depends(get_playlist_item_repository),
]
MediaAssetRepositoryDependency = Annotated[
    MediaAssetRepository,
    Depends(get_media_asset_repository),
]
ScreenPlaylistAssignmentRepositoryDependency = Annotated[
    ScreenPlaylistAssignmentRepository,
    Depends(get_screen_playlist_assignment_repository),
]
ScreenSyncStateRepositoryDependency = Annotated[
    ScreenSyncStateRepository,
    Depends(get_screen_sync_state_repository),
]


def get_create_playlist_use_case(
    playlist_repository: PlaylistRepositoryDependency,
    playlist_item_repository: PlaylistItemRepositoryDependency,
    media_repository: MediaAssetRepositoryDependency,
) -> CreatePlaylistUseCase:
    return CreatePlaylistUseCase(
        playlist_repository=playlist_repository,
        playlist_item_repository=playlist_item_repository,
        media_repository=media_repository,
    )


CreatePlaylist = Annotated[
    CreatePlaylistUseCase,
    Depends(get_create_playlist_use_case),
]


def get_get_playlist_use_case(
    playlist_repository: PlaylistRepositoryDependency,
) -> GetPlaylistUseCase:
    return GetPlaylistUseCase(playlist_repository=playlist_repository)


GetPlaylist = Annotated[
    GetPlaylistUseCase,
    Depends(get_get_playlist_use_case),
]


def get_list_playlists_use_case(
    playlist_repository: PlaylistRepositoryDependency,
) -> ListPlaylistsUseCase:
    return ListPlaylistsUseCase(playlist_repository=playlist_repository)


ListPlaylists = Annotated[
    ListPlaylistsUseCase,
    Depends(get_list_playlists_use_case),
]


def get_update_playlist_use_case(
    playlist_repository: PlaylistRepositoryDependency,
    playlist_item_repository: PlaylistItemRepositoryDependency,
    media_repository: MediaAssetRepositoryDependency,
    assignment_repository: ScreenPlaylistAssignmentRepositoryDependency,
    sync_state_repository: ScreenSyncStateRepositoryDependency,
) -> UpdatePlaylistUseCase:
    return UpdatePlaylistUseCase(
        playlist_repository=playlist_repository,
        playlist_item_repository=playlist_item_repository,
        media_repository=media_repository,
        assignment_repository=assignment_repository,
        sync_state_repository=sync_state_repository,
    )


UpdatePlaylist = Annotated[
    UpdatePlaylistUseCase,
    Depends(get_update_playlist_use_case),
]


def get_delete_playlist_use_case(
    playlist_repository: PlaylistRepositoryDependency,
    assignment_repository: ScreenPlaylistAssignmentRepositoryDependency,
    sync_state_repository: ScreenSyncStateRepositoryDependency,
) -> DeletePlaylistUseCase:
    return DeletePlaylistUseCase(
        playlist_repository=playlist_repository,
        assignment_repository=assignment_repository,
        sync_state_repository=sync_state_repository,
    )


DeletePlaylist = Annotated[
    DeletePlaylistUseCase,
    Depends(get_delete_playlist_use_case),
]
