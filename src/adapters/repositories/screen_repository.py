"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session
from adapters.repositories.mappers import (
    apply_screen,
    to_screen,
)
from domain.entities.entities import (
    Screen,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    ScreenModel,
)


class SqlAlchemyScreenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, screen_id: UUID) -> Screen | None:
        model = await self.session.get(ScreenModel, screen_id)
        return to_screen(model) if model else None

    async def get_by_screen_code(self, screen_code: str) -> Screen | None:
        model = await self.session.scalar(
            select(ScreenModel).where(ScreenModel.screen_code == screen_code)
        )
        return to_screen(model) if model else None

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[Screen]:
        result = await self.session.scalars(
            select(ScreenModel).order_by(ScreenModel.created_at).offset(offset).limit(limit)
        )
        return [to_screen(model) for model in result]

    async def save(self, screen: Screen) -> Screen:
        model = ScreenModel()
        apply_screen(screen, model)
        self.session.add(model)
        await flush_session(self.session, "screen save")
        return to_screen(model)

    async def update(self, screen: Screen) -> Screen:
        model = await self.session.get(ScreenModel, screen.id)
        if model is None:
            raise PersistenceError("screen was not found")
        apply_screen(screen, model)
        await flush_session(self.session, "screen update")
        return to_screen(model)
