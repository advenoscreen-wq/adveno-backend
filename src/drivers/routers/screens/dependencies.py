"""Dependencies for screen management routes."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.media_asset_repository import SqlAlchemyMediaAssetRepository
from adapters.repositories.playlist_item_repository import SqlAlchemyPlaylistItemRepository
from adapters.repositories.playlist_repository import SqlAlchemyPlaylistRepository
from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from adapters.repositories.screen_playlist_assignment_repository import (
    SqlAlchemyScreenPlaylistAssignmentRepository,
)
from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from adapters.repositories.screen_sync_state_repository import SqlAlchemyScreenSyncStateRepository
from application.exceptions.authentication import InvalidScreenCredentialError
from application.use_cases.screens.assign_playlist_use_case import AssignPlaylistUseCase
from application.use_cases.screens.check_screen_sync_use_case import CheckScreenSyncUseCase
from application.use_cases.screens.delete_screen_use_case import DeleteScreenUseCase
from application.use_cases.screens.disconnect_screen_use_case import DisconnectScreenUseCase
from application.use_cases.screens.get_assigned_playlist_use_case import (
    GetAssignedPlaylistUseCase,
)
from application.use_cases.screens.get_screen_use_case import GetScreenUseCase
from application.use_cases.screens.list_screens_use_case import ListScreensUseCase
from application.use_cases.screens.unassign_playlist_use_case import UnassignPlaylistUseCase
from application.use_cases.screens.update_screen_use_case import UpdateScreenUseCase
from drivers.database.database import session_dependency
from drivers.routers.dependencies import SettingsDependency
from drivers.routers.media.dependencies import StorageServiceDependency
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.repositories.playlist_item_repository import PlaylistItemRepository
from ports.repositories.playlist_repository import PlaylistRepository
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_repository import ScreenRepository
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


def get_screen_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenRepository:
    """Build the request-scoped screen repository."""
    return SqlAlchemyScreenRepository(session)


ScreenRepositoryDependency = Annotated[
    ScreenRepository,
    Depends(get_screen_repository),
]


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


def get_assignment_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenPlaylistAssignmentRepository:
    return SqlAlchemyScreenPlaylistAssignmentRepository(session)


def get_sync_state_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenSyncStateRepository:
    return SqlAlchemyScreenSyncStateRepository(session)


def get_screen_credential_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenCredentialRepository:
    return SqlAlchemyScreenCredentialRepository(session)


def get_update_screen_use_case(
    repository: ScreenRepositoryDependency,
) -> UpdateScreenUseCase:
    return UpdateScreenUseCase(repository=repository)


UpdateScreen = Annotated[UpdateScreenUseCase, Depends(get_update_screen_use_case)]


def get_check_screen_sync_use_case(
    screen_repository: ScreenRepositoryDependency,
    credential_repository: Annotated[
        ScreenCredentialRepository,
        Depends(get_screen_credential_repository),
    ],
    sync_state_repository: Annotated[
        ScreenSyncStateRepository,
        Depends(get_sync_state_repository),
    ],
) -> CheckScreenSyncUseCase:
    return CheckScreenSyncUseCase(
        screen_repository=screen_repository,
        credential_repository=credential_repository,
        sync_state_repository=sync_state_repository,
    )


CheckScreenSync = Annotated[
    CheckScreenSyncUseCase,
    Depends(get_check_screen_sync_use_case),
]


def get_assigned_playlist_use_case(
    screen_repository: ScreenRepositoryDependency,
    credential_repository: Annotated[
        ScreenCredentialRepository,
        Depends(get_screen_credential_repository),
    ],
    assignment_repository: Annotated[
        ScreenPlaylistAssignmentRepository,
        Depends(get_assignment_repository),
    ],
    playlist_repository: Annotated[PlaylistRepository, Depends(get_playlist_repository)],
    playlist_item_repository: Annotated[
        PlaylistItemRepository,
        Depends(get_playlist_item_repository),
    ],
    media_repository: Annotated[MediaAssetRepository, Depends(get_media_asset_repository)],
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> GetAssignedPlaylistUseCase:
    return GetAssignedPlaylistUseCase(
        screen_repository=screen_repository,
        credential_repository=credential_repository,
        assignment_repository=assignment_repository,
        playlist_repository=playlist_repository,
        playlist_item_repository=playlist_item_repository,
        media_repository=media_repository,
        storage_service=storage_service,
        bucket=settings.media_storage_bucket,
    )


GetAssignedPlaylist = Annotated[
    GetAssignedPlaylistUseCase,
    Depends(get_assigned_playlist_use_case),
]


async def get_screen_device_credential(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(HTTPBearer(auto_error=False)),
    ],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidScreenCredentialError()
    return credentials.credentials


ScreenDeviceCredential = Annotated[str, Depends(get_screen_device_credential)]


def get_list_screens_use_case(
    screen_repository: ScreenRepositoryDependency,
) -> ListScreensUseCase:
    return ListScreensUseCase(screen_repository=screen_repository)


ListScreens = Annotated[ListScreensUseCase, Depends(get_list_screens_use_case)]


def get_get_screen_use_case(
    screen_repository: ScreenRepositoryDependency,
    playlist_repository: Annotated[PlaylistRepository, Depends(get_playlist_repository)],
    assignment_repository: Annotated[
        ScreenPlaylistAssignmentRepository,
        Depends(get_assignment_repository),
    ],
) -> GetScreenUseCase:
    return GetScreenUseCase(
        screen_repository=screen_repository,
        playlist_repository=playlist_repository,
        assignment_repository=assignment_repository,
    )


GetScreen = Annotated[GetScreenUseCase, Depends(get_get_screen_use_case)]


def get_assign_playlist_use_case(
    screen_repository: ScreenRepositoryDependency,
    playlist_repository: Annotated[PlaylistRepository, Depends(get_playlist_repository)],
    assignment_repository: Annotated[
        ScreenPlaylistAssignmentRepository,
        Depends(get_assignment_repository),
    ],
    sync_state_repository: Annotated[
        ScreenSyncStateRepository,
        Depends(get_sync_state_repository),
    ],
) -> AssignPlaylistUseCase:
    return AssignPlaylistUseCase(
        screen_repository=screen_repository,
        playlist_repository=playlist_repository,
        assignment_repository=assignment_repository,
        sync_state_repository=sync_state_repository,
    )


AssignPlaylist = Annotated[AssignPlaylistUseCase, Depends(get_assign_playlist_use_case)]


def get_unassign_playlist_use_case(
    screen_repository: ScreenRepositoryDependency,
    assignment_repository: Annotated[
        ScreenPlaylistAssignmentRepository,
        Depends(get_assignment_repository),
    ],
    sync_state_repository: Annotated[
        ScreenSyncStateRepository,
        Depends(get_sync_state_repository),
    ],
) -> UnassignPlaylistUseCase:
    return UnassignPlaylistUseCase(
        screen_repository=screen_repository,
        assignment_repository=assignment_repository,
        sync_state_repository=sync_state_repository,
    )


UnassignPlaylist = Annotated[
    UnassignPlaylistUseCase,
    Depends(get_unassign_playlist_use_case),
]


def get_delete_screen_use_case(
    screen_repository: ScreenRepositoryDependency,
) -> DeleteScreenUseCase:
    return DeleteScreenUseCase(screen_repository=screen_repository)


DeleteScreen = Annotated[DeleteScreenUseCase, Depends(get_delete_screen_use_case)]


def get_disconnect_screen_use_case(
    screen_repository: ScreenRepositoryDependency,
    credential_repository: Annotated[
        ScreenCredentialRepository,
        Depends(get_screen_credential_repository),
    ],
) -> DisconnectScreenUseCase:
    return DisconnectScreenUseCase(
        screen_repository=screen_repository,
        credential_repository=credential_repository,
    )


DisconnectScreen = Annotated[
    DisconnectScreenUseCase,
    Depends(get_disconnect_screen_use_case),
]
