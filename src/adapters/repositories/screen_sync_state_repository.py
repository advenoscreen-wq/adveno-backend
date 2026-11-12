"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session
from adapters.repositories.mappers import (
    apply_sync_state,
    to_sync_state,
)
from domain.entities.entities import (
    ScreenSyncState,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    ScreenSyncStateModel,
)


class SqlAlchemyScreenSyncStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_screen_id(self, screen_id: UUID) -> ScreenSyncState | None:
        model = await self.session.get(ScreenSyncStateModel, screen_id)
        return to_sync_state(model) if model else None

    async def save(self, state: ScreenSyncState) -> ScreenSyncState:
        model = ScreenSyncStateModel()
        apply_sync_state(state, model)
        self.session.add(model)
        await flush_session(self.session, "screen sync state save")
        return to_sync_state(model)

    async def update(self, state: ScreenSyncState) -> ScreenSyncState:
        model = await self.session.get(ScreenSyncStateModel, state.screen_id)
        if model is None:
            raise PersistenceError("screen sync state was not found")
        apply_sync_state(state, model)
        await flush_session(self.session, "screen sync state update")
        return to_sync_state(model)
