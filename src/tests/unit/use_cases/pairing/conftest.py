"""Fixtures for pairing use-case tests."""

from datetime import datetime
from uuid import UUID

import pytest

from application.use_cases.pairing.create_screen_pairing_session_use_case import (
    CreateScreenPairingSessionUseCase,
)
from application.use_cases.pairing.verify_screen_pairing_session_use_case import (
    VerifyScreenPairingSessionUseCase,
)
from domain import ScreenPairingSession


class FakeScreenPairingSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[UUID, ScreenPairingSession] = {}

    async def get_by_id(self, session_id: UUID) -> ScreenPairingSession | None:
        return self.sessions.get(session_id)

    async def get_by_token_hash(self, token_hash: str) -> ScreenPairingSession | None:
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
