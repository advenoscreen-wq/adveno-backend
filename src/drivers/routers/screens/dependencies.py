"""Dependencies for screen management routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from application.use_cases.screens.update_screen_use_case import UpdateScreenUseCase
from drivers.database.database import session_dependency
from ports.repositories.screen_repository import ScreenRepository


def get_screen_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenRepository:
    """Build the request-scoped screen repository."""
    return SqlAlchemyScreenRepository(session)


ScreenRepositoryDependency = Annotated[
    ScreenRepository,
    Depends(get_screen_repository),
]


def get_update_screen_use_case(
    repository: ScreenRepositoryDependency,
) -> UpdateScreenUseCase:
    return UpdateScreenUseCase(repository=repository)


UpdateScreen = Annotated[UpdateScreenUseCase, Depends(get_update_screen_use_case)]
