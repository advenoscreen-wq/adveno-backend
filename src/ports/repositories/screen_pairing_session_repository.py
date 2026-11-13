from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from domain import (
    ScreenPairingSession,
)


class ScreenPairingSessionRepository(Protocol):
    async def get_by_id(self, session_id: UUID) -> ScreenPairingSession | None: ...

    async def get_by_token_hash(self, token_hash: str) -> ScreenPairingSession | None: ...

    async def get_valid_session(
        self, token_hash: str, *, at: datetime | None = None
    ) -> ScreenPairingSession | None: ...

    async def save(self, session: ScreenPairingSession) -> ScreenPairingSession: ...

    async def update(self, session: ScreenPairingSession) -> ScreenPairingSession: ...
