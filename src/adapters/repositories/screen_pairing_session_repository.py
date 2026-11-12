"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session
from adapters.repositories.mappers import (
    apply_pairing_session,
    to_pairing_session,
)
from domain.entities.entities import (
    ScreenPairingSession,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    ScreenPairingSessionModel,
)


class SqlAlchemyScreenPairingSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, session_id: UUID) -> ScreenPairingSession | None:
        model = await self.session.get(ScreenPairingSessionModel, session_id)
        return to_pairing_session(model) if model else None

    async def get_valid_session(
        self, token_hash: str, *, at: datetime | None = None
    ) -> ScreenPairingSession | None:
        check_at = at or datetime.now(UTC)
        model = await self.session.scalar(
            select(ScreenPairingSessionModel).where(
                ScreenPairingSessionModel.token_hash == token_hash,
                ScreenPairingSessionModel.paired_at.is_(None),
                ScreenPairingSessionModel.expires_at > check_at,
            )
        )
        return to_pairing_session(model) if model else None

    async def save(self, session: ScreenPairingSession) -> ScreenPairingSession:
        model = ScreenPairingSessionModel()
        apply_pairing_session(session, model)
        self.session.add(model)
        await flush_session(self.session, "pairing session save")
        return to_pairing_session(model)

    async def update(self, session: ScreenPairingSession) -> ScreenPairingSession:
        model = await self.session.get(ScreenPairingSessionModel, session.id)
        if model is None:
            raise PersistenceError("pairing session was not found")
        apply_pairing_session(session, model)
        await flush_session(self.session, "pairing session update")
        return to_pairing_session(model)
