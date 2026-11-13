"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session, log_repository_operations
from adapters.repositories.mappers import (
    apply_assignment,
    to_assignment,
)
from domain.entities.entities import (
    ScreenPlaylistAssignment,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    PlaylistModel,
    ScreenModel,
    ScreenPlaylistAssignmentModel,
)


@log_repository_operations
class SqlAlchemyScreenPlaylistAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _validate_ownership(self, assignment: ScreenPlaylistAssignment) -> None:
        owners = await self.session.execute(
            select(ScreenModel.user_id, PlaylistModel.user_id)
            .join(PlaylistModel, PlaylistModel.id == assignment.playlist_id)
            .where(ScreenModel.id == assignment.screen_id)
        )
        row = owners.one_or_none()
        if row is None:
            raise PersistenceError("screen or playlist was not found")
        if row[0] != row[1]:
            raise PersistenceError("screen and playlist belong to different users")

    async def get_active_by_screen_id(self, screen_id: UUID) -> ScreenPlaylistAssignment | None:
        model = await self.session.scalar(
            select(ScreenPlaylistAssignmentModel).where(
                ScreenPlaylistAssignmentModel.screen_id == screen_id,
                ScreenPlaylistAssignmentModel.unassigned_at.is_(None),
            )
        )
        return to_assignment(model) if model else None

    async def list_by_screen_id(
        self, screen_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[ScreenPlaylistAssignment]:
        result = await self.session.scalars(
            select(ScreenPlaylistAssignmentModel)
            .where(ScreenPlaylistAssignmentModel.screen_id == screen_id)
            .order_by(ScreenPlaylistAssignmentModel.assigned_at)
            .offset(offset)
            .limit(limit)
        )
        return [to_assignment(model) for model in result]

    async def list_by_playlist_id(
        self, playlist_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[ScreenPlaylistAssignment]:
        result = await self.session.scalars(
            select(ScreenPlaylistAssignmentModel)
            .where(ScreenPlaylistAssignmentModel.playlist_id == playlist_id)
            .order_by(ScreenPlaylistAssignmentModel.assigned_at)
            .offset(offset)
            .limit(limit)
        )
        return [to_assignment(model) for model in result]

    async def save(self, assignment: ScreenPlaylistAssignment) -> ScreenPlaylistAssignment:
        await self._validate_ownership(assignment)
        model = ScreenPlaylistAssignmentModel()
        apply_assignment(assignment, model)
        self.session.add(model)
        await flush_session(self.session, "screen playlist assignment save")
        return to_assignment(model)

    async def update(self, assignment: ScreenPlaylistAssignment) -> ScreenPlaylistAssignment:
        await self._validate_ownership(assignment)
        model = await self.session.get(ScreenPlaylistAssignmentModel, assignment.id)
        if model is None:
            raise PersistenceError("screen playlist assignment was not found")
        apply_assignment(assignment, model)
        await flush_session(self.session, "screen playlist assignment update")
        return to_assignment(model)
