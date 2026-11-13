"""Dependencies for screen pairing routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.screen_pairing_session_repository import (
    SqlAlchemyScreenPairingSessionRepository,
)
from application.use_cases.pairing.create_screen_pairing_session_use_case import (
    CreateScreenPairingSessionUseCase,
)
from application.use_cases.pairing.get_screen_pairing_session_status_use_case import (
    GetScreenPairingSessionStatusUseCase,
)
from application.use_cases.pairing.verify_screen_pairing_session_use_case import (
    VerifyScreenPairingSessionUseCase,
)
from drivers.database.database import session_dependency
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)


def get_screen_pairing_session_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenPairingSessionRepository:
    """Build the request-scoped pairing session repository."""
    return SqlAlchemyScreenPairingSessionRepository(session)


ScreenPairingSessionRepositoryDependency = Annotated[
    ScreenPairingSessionRepository,
    Depends(get_screen_pairing_session_repository),
]


def get_create_screen_pairing_session_use_case(
    repository: ScreenPairingSessionRepositoryDependency,
) -> CreateScreenPairingSessionUseCase:
    """Build the pairing session creation use case."""
    return CreateScreenPairingSessionUseCase(repository=repository)


def get_screen_pairing_session_status_use_case(
    repository: ScreenPairingSessionRepositoryDependency,
) -> GetScreenPairingSessionStatusUseCase:
    """Build the pairing session status use case."""
    return GetScreenPairingSessionStatusUseCase(repository=repository)


def get_verify_screen_pairing_session_use_case(
    repository: ScreenPairingSessionRepositoryDependency,
) -> VerifyScreenPairingSessionUseCase:
    """Build the authenticated pairing session verification use case."""
    return VerifyScreenPairingSessionUseCase(repository=repository)


CreateScreenPairingSession = Annotated[
    CreateScreenPairingSessionUseCase,
    Depends(get_create_screen_pairing_session_use_case),
]
GetScreenPairingSessionStatus = Annotated[
    GetScreenPairingSessionStatusUseCase,
    Depends(get_screen_pairing_session_status_use_case),
]
VerifyScreenPairingSession = Annotated[
    VerifyScreenPairingSessionUseCase,
    Depends(get_verify_screen_pairing_session_use_case),
]
