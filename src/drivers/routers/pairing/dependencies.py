"""Dependencies for screen pairing routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from adapters.repositories.screen_pairing_session_repository import (
    SqlAlchemyScreenPairingSessionRepository,
)
from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from adapters.repositories.screen_sync_state_repository import (
    SqlAlchemyScreenSyncStateRepository,
)
from application.use_cases.pairing.approve_screen_pairing_session_use_case import (
    ApproveScreenPairingSessionUseCase,
)
from application.use_cases.pairing.create_paired_screen_use_case import (
    CreatePairedScreenUseCase,
)
from application.use_cases.pairing.create_screen_pairing_session_use_case import (
    CreateScreenPairingSessionUseCase,
)
from application.use_cases.pairing.get_screen_pairing_session_status_use_case import (
    GetScreenPairingSessionStatusUseCase,
)
from application.use_cases.pairing.issue_paired_screen_credential_use_case import (
    IssuePairedScreenCredentialUseCase,
)
from application.use_cases.pairing.verify_screen_pairing_session_use_case import (
    VerifyScreenPairingSessionUseCase,
)
from drivers.database.database import session_dependency
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)
from ports.repositories.screen_repository import ScreenRepository
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


def get_screen_pairing_session_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenPairingSessionRepository:
    """Build the request-scoped pairing session repository."""
    return SqlAlchemyScreenPairingSessionRepository(session)


def get_screen_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenRepository:
    """Build the request-scoped screen repository."""
    return SqlAlchemyScreenRepository(session)


def get_screen_credential_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenCredentialRepository:
    """Build the request-scoped screen credential repository."""
    return SqlAlchemyScreenCredentialRepository(session)


def get_screen_sync_state_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ScreenSyncStateRepository:
    """Build the request-scoped screen sync state repository."""
    return SqlAlchemyScreenSyncStateRepository(session)


ScreenPairingSessionRepositoryDependency = Annotated[
    ScreenPairingSessionRepository,
    Depends(get_screen_pairing_session_repository),
]
ScreenRepositoryDependency = Annotated[ScreenRepository, Depends(get_screen_repository)]


def get_create_screen_pairing_session_use_case(
    repository: ScreenPairingSessionRepositoryDependency,
) -> CreateScreenPairingSessionUseCase:
    """Build the pairing session creation use case."""
    return CreateScreenPairingSessionUseCase(repository=repository)


def get_approve_screen_pairing_session_use_case(
    pairing_session_repository: ScreenPairingSessionRepositoryDependency,
    screen_repository: ScreenRepositoryDependency,
    credential_repository: Annotated[
        ScreenCredentialRepository, Depends(get_screen_credential_repository)
    ],
) -> ApproveScreenPairingSessionUseCase:
    """Build the pairing approval use case."""
    return ApproveScreenPairingSessionUseCase(
        pairing_session_repository=pairing_session_repository,
        screen_repository=screen_repository,
        screen_credential_repository=credential_repository,
    )


def get_create_paired_screen_use_case(
    pairing_session_repository: ScreenPairingSessionRepositoryDependency,
    screen_repository: ScreenRepositoryDependency,
    credential_repository: Annotated[
        ScreenCredentialRepository, Depends(get_screen_credential_repository)
    ],
    sync_state_repository: Annotated[
        ScreenSyncStateRepository, Depends(get_screen_sync_state_repository)
    ],
) -> CreatePairedScreenUseCase:
    """Build the screen registration use case for completed pairings."""
    return CreatePairedScreenUseCase(
        pairing_session_repository=pairing_session_repository,
        screen_repository=screen_repository,
        screen_credential_repository=credential_repository,
        screen_sync_state_repository=sync_state_repository,
    )


def get_issue_paired_screen_credential_use_case(
    pairing_session_repository: ScreenPairingSessionRepositoryDependency,
    credential_repository: Annotated[
        ScreenCredentialRepository, Depends(get_screen_credential_repository)
    ],
) -> IssuePairedScreenCredentialUseCase:
    """Build the paired screen credential rotation use case."""
    return IssuePairedScreenCredentialUseCase(
        pairing_session_repository=pairing_session_repository,
        screen_credential_repository=credential_repository,
    )


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
ApproveScreenPairingSession = Annotated[
    ApproveScreenPairingSessionUseCase,
    Depends(get_approve_screen_pairing_session_use_case),
]
CreatePairedScreen = Annotated[
    CreatePairedScreenUseCase,
    Depends(get_create_paired_screen_use_case),
]
IssuePairedScreenCredential = Annotated[
    IssuePairedScreenCredentialUseCase,
    Depends(get_issue_paired_screen_credential_use_case),
]
GetScreenPairingSessionStatus = Annotated[
    GetScreenPairingSessionStatusUseCase,
    Depends(get_screen_pairing_session_status_use_case),
]
VerifyScreenPairingSession = Annotated[
    VerifyScreenPairingSessionUseCase,
    Depends(get_verify_screen_pairing_session_use_case),
]
