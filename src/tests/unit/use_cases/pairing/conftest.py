"""Fixtures for pairing use-case tests."""

from datetime import datetime
from uuid import UUID

import pytest

from application.use_cases.pairing.approve_screen_pairing_session_use_case import (
    ApproveScreenPairingSessionUseCase,
)
from application.use_cases.pairing.check_pairing_completion_use_case import (
    CheckPairingCompletionUseCase,
)
from application.use_cases.pairing.create_paired_screen_use_case import (
    CreatePairedScreenUseCase,
)
from application.use_cases.pairing.create_screen_pairing_session_use_case import (
    CreateScreenPairingSessionUseCase,
)
from application.use_cases.pairing.issue_paired_screen_credential_use_case import (
    IssuePairedScreenCredentialUseCase,
)
from application.use_cases.pairing.verify_screen_pairing_session_use_case import (
    VerifyScreenPairingSessionUseCase,
)
from domain import Screen, ScreenCredential, ScreenPairingSession


class FakeScreenPairingSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[UUID, ScreenPairingSession] = {}

    async def get_by_id(
        self, session_id: UUID, *, for_update: bool = False
    ) -> ScreenPairingSession | None:
        return self.sessions.get(session_id)

    async def get_by_token_hash(
        self, token_hash: str, *, for_update: bool = False
    ) -> ScreenPairingSession | None:
        return next(
            (session for session in self.sessions.values() if session.token_hash == token_hash),
            None,
        )

    async def get_valid_session(
        self, token_hash: str, *, at: datetime | None = None
    ) -> ScreenPairingSession | None:
        return next(
            (
                session
                for session in self.sessions.values()
                if session.token_hash == token_hash and session.is_valid(at=at)
            ),
            None,
        )

    async def save(self, session: ScreenPairingSession) -> ScreenPairingSession:
        self.sessions[session.id] = session
        return session

    async def update(self, session: ScreenPairingSession) -> ScreenPairingSession:
        self.sessions[session.id] = session
        return session


class FakeScreenRepository:
    def __init__(self) -> None:
        self.screens: dict[UUID, Screen] = {}

    async def get_by_id(self, screen_id: UUID, *, user_id: UUID | None = None) -> Screen | None:
        screen = self.screens.get(screen_id)
        if screen is not None and user_id is not None and screen.user_id != user_id:
            return None
        return screen

    async def get_by_screen_code(
        self, screen_code: str, *, user_id: UUID | None = None
    ) -> Screen | None:
        raise NotImplementedError

    async def list_all(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[Screen]:
        raise NotImplementedError

    async def list_by_user_id(
        self, user_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[Screen]:
        raise NotImplementedError

    async def save(self, screen: Screen) -> Screen:
        self.screens[screen.id] = screen
        return screen

    async def update(self, screen: Screen) -> Screen:
        self.screens[screen.id] = screen
        return screen


class FakeScreenCredentialRepository:
    def __init__(self) -> None:
        self.credentials: dict[UUID, ScreenCredential] = {}

    async def get_by_id(self, credential_id: UUID) -> ScreenCredential | None:
        return self.credentials.get(credential_id)

    async def get_active_credential_by_screen(
        self, screen_id: UUID, *, for_update: bool = False
    ) -> ScreenCredential | None:
        return next(
            (
                credential
                for credential in self.credentials.values()
                if credential.screen_id == screen_id and credential.revoked_at is None
            ),
            None,
        )

    async def get_active_credentials_by_screen(
        self, screen_id: UUID
    ) -> list[ScreenCredential]:
        return [
            credential
            for credential in self.credentials.values()
            if credential.screen_id == screen_id and credential.revoked_at is None
        ]

    async def save(self, credential: ScreenCredential) -> ScreenCredential:
        if await self.get_active_credential_by_screen(credential.screen_id):
            raise AssertionError("screen already has an active credential")
        self.credentials[credential.id] = credential
        return credential

    async def update(self, credential: ScreenCredential) -> ScreenCredential:
        self.credentials[credential.id] = credential
        return credential


@pytest.fixture
def fake_screen_pairing_session_repository() -> FakeScreenPairingSessionRepository:
    return FakeScreenPairingSessionRepository()


@pytest.fixture
def create_screen_pairing_session_use_case(
    fake_screen_pairing_session_repository: FakeScreenPairingSessionRepository,
) -> CreateScreenPairingSessionUseCase:
    return CreateScreenPairingSessionUseCase(
        repository=fake_screen_pairing_session_repository
    )


@pytest.fixture
def verify_screen_pairing_session_use_case(
    fake_screen_pairing_session_repository: FakeScreenPairingSessionRepository,
) -> VerifyScreenPairingSessionUseCase:
    return VerifyScreenPairingSessionUseCase(
        repository=fake_screen_pairing_session_repository
    )


@pytest.fixture
def fake_screen_repository() -> FakeScreenRepository:
    return FakeScreenRepository()


@pytest.fixture
def fake_screen_credential_repository() -> FakeScreenCredentialRepository:
    return FakeScreenCredentialRepository()


@pytest.fixture
def approve_screen_pairing_session_use_case(
    fake_screen_pairing_session_repository: FakeScreenPairingSessionRepository,
    fake_screen_repository: FakeScreenRepository,
    fake_screen_credential_repository: FakeScreenCredentialRepository,
) -> ApproveScreenPairingSessionUseCase:
    return ApproveScreenPairingSessionUseCase(
        pairing_session_repository=fake_screen_pairing_session_repository,
        screen_repository=fake_screen_repository,
        screen_credential_repository=fake_screen_credential_repository,
    )


@pytest.fixture
def create_paired_screen_use_case(
    fake_screen_pairing_session_repository: FakeScreenPairingSessionRepository,
    fake_screen_repository: FakeScreenRepository,
    fake_screen_credential_repository: FakeScreenCredentialRepository,
) -> CreatePairedScreenUseCase:
    return CreatePairedScreenUseCase(
        pairing_session_repository=fake_screen_pairing_session_repository,
        screen_repository=fake_screen_repository,
        screen_credential_repository=fake_screen_credential_repository,
    )


@pytest.fixture
def issue_paired_screen_credential_use_case(
    fake_screen_pairing_session_repository: FakeScreenPairingSessionRepository,
    fake_screen_credential_repository: FakeScreenCredentialRepository,
) -> IssuePairedScreenCredentialUseCase:
    return IssuePairedScreenCredentialUseCase(
        pairing_session_repository=fake_screen_pairing_session_repository,
        screen_credential_repository=fake_screen_credential_repository,
    )


@pytest.fixture
def check_pairing_completion_use_case(
    fake_screen_pairing_session_repository: FakeScreenPairingSessionRepository,
    fake_screen_credential_repository: FakeScreenCredentialRepository,
) -> CheckPairingCompletionUseCase:
    return CheckPairingCompletionUseCase(
        pairing_session_repository=fake_screen_pairing_session_repository,
        screen_credential_repository=fake_screen_credential_repository,
    )
