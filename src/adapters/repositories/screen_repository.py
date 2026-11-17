"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session, log_repository_operations
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


@log_repository_operations
class SqlAlchemyScreenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, screen_id: UUID, *, user_id: UUID | None = None) -> Screen | None:
        statement = select(ScreenModel).where(ScreenModel.id == screen_id)
        if user_id is not None:
            statement = statement.where(ScreenModel.user_id == user_id)
        model = await self.session.scalar(statement)
        return to_screen(model) if model else None

    async def get_by_screen_code(
        self, screen_code: str, *, user_id: UUID | None = None
    ) -> Screen | None:
        statement = select(ScreenModel).where(ScreenModel.screen_code == screen_code)
        if user_id is not None:
            statement = statement.where(ScreenModel.user_id == user_id)
        model = await self.session.scalar(statement)
        return to_screen(model) if model else None

    async def list_all(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[Screen]:
        statement = select(ScreenModel)
        if user_id is not None:
            statement = statement.where(ScreenModel.user_id == user_id)
        result = await self.session.scalars(
            statement.order_by(ScreenModel.created_at, ScreenModel.id).offset(offset).limit(limit)
        )
        return [to_screen(model) for model in result]

    async def list_by_user_id(
        self,
        user_id: UUID,
        *,
        filter_by_name: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Screen]:
        statement = select(ScreenModel).where(ScreenModel.user_id == user_id)
        if filter_by_name:
            statement = statement.where(ScreenModel.name.ilike(f"%{filter_by_name}%"))
        result = await self.session.scalars(
            statement.order_by(ScreenModel.created_at, ScreenModel.id).offset(offset).limit(limit)
        )
        return [to_screen(model) for model in result]

    async def count_by_user_id(self, user_id: UUID, *, filter_by_name: str | None = None) -> int:
        statement = select(func.count(ScreenModel.id)).where(ScreenModel.user_id == user_id)
        if filter_by_name:
            statement = statement.where(ScreenModel.name.ilike(f"%{filter_by_name}%"))
        return int(await self.session.scalar(statement) or 0)

    async def save(self, screen: Screen) -> Screen:
        model = ScreenModel()
        apply_screen(screen, model)
        self.session.add(model)
        await flush_session(self.session, "screen save")
        return to_screen(model)

    async def update(self, screen: Screen) -> Screen:
        model = await self.session.scalar(
            select(ScreenModel).where(
                ScreenModel.id == screen.id, ScreenModel.user_id == screen.user_id
            )
        )
        if model is None:
            raise PersistenceError("screen was not found")
        apply_screen(screen, model)
        await flush_session(self.session, "screen update")
        return to_screen(model)
