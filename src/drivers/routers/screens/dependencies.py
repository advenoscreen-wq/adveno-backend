"""Dependencies for screen management routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.playlist_repository import SqlAlchemyPlaylistRepository
from adapters.repositories.screen_playlist_assignment_repository import (
    SqlAlchemyScreenPlaylistAssignmentRepository,
)
from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from adapters.repositories.screen_sync_state_repository import SqlAlchemyScreenSyncStateRepository
from application.use_cases.screens.assign_playlist_use_case import AssignPlaylistUseCase
from application.use_cases.screens.get_screen_use_case import GetScreenUseCase
from application.use_cases.screens.list_screens_use_case import ListScreensUseCase
from application.use_cases.screens.update_screen_use_case import UpdateScreenUseCase
from drivers.database.database import session_dependency
from ports.repositories.playlist_repository import PlaylistRepository
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


def get_assignment_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenPlaylistAssignmentRepository:
    return SqlAlchemyScreenPlaylistAssignmentRepository(session)


def get_sync_state_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenSyncStateRepository:
    return SqlAlchemyScreenSyncStateRepository(session)


def get_update_screen_use_case(
    repository: ScreenRepositoryDependency,
) -> UpdateScreenUseCase:
    return UpdateScreenUseCase(repository=repository)


UpdateScreen = Annotated[UpdateScreenUseCase, Depends(get_update_screen_use_case)]


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
