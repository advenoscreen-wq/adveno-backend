"""SQLAlchemy persistence adapter for screen-admin sessions."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session, log_repository_operations
from domain import ScreenAdminSession
from drivers.database.models.screen_admin_session import ScreenAdminSessionModel


def _to_entity(model: ScreenAdminSessionModel) -> ScreenAdminSession:
    return ScreenAdminSession(
        id=model.id,
        screen_id=model.screen_id,
        code_hash=model.code_hash,
        token_hash=model.token_hash,
        created_at=model.created_at,
        last_activity_at=model.last_activity_at,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
    )


@log_repository_operations
class SqlAlchemyScreenAdminSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_pending_pin_by_screen_id(
        self, screen_id: UUID, *, for_update: bool = False
    ) -> ScreenAdminSession | None:
        statement = (
            select(ScreenAdminSessionModel)
            .where(
                ScreenAdminSessionModel.screen_id == screen_id,
                ScreenAdminSessionModel.token_hash.is_(None),
                ScreenAdminSessionModel.revoked_at.is_(None),
            )
            .order_by(ScreenAdminSessionModel.created_at.desc())
            .limit(1)
        )
        if for_update:
            statement = statement.with_for_update()
        model = await self.session.scalar(statement)
        return _to_entity(model) if model is not None else None

    async def get_by_screen_id_and_token_hash(
        self, screen_id: UUID, token_hash: str, *, for_update: bool = False
    ) -> ScreenAdminSession | None:
        statement = select(ScreenAdminSessionModel).where(
            ScreenAdminSessionModel.screen_id == screen_id,
            ScreenAdminSessionModel.token_hash == token_hash,
        )
        if for_update:
            statement = statement.with_for_update()
        model = await self.session.scalar(statement)
        return _to_entity(model) if model is not None else None

    async def save(self, session: ScreenAdminSession) -> ScreenAdminSession:
        model = ScreenAdminSessionModel(
            id=session.id,
            screen_id=session.screen_id,
            code_hash=session.code_hash,
            token_hash=session.token_hash,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )
        self.session.add(model)
        await flush_session(self.session, "screen admin session save")
        return _to_entity(model)

    async def update(self, session: ScreenAdminSession) -> ScreenAdminSession:
        model = await self.session.get(ScreenAdminSessionModel, session.id)
        if model is None:
            raise RuntimeError("screen admin session was not found")
        model.code_hash = session.code_hash
        model.token_hash = session.token_hash
        model.last_activity_at = session.last_activity_at
        model.expires_at = session.expires_at
        model.revoked_at = session.revoked_at
        await flush_session(self.session, "screen admin session update")
        return _to_entity(model)

    async def revoke_pending_by_screen_id(self, screen_id: UUID, *, at: datetime) -> None:
        await self.session.execute(
            update(ScreenAdminSessionModel)
            .where(
                ScreenAdminSessionModel.screen_id == screen_id,
                ScreenAdminSessionModel.token_hash.is_(None),
                ScreenAdminSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=at)
        )
        await self.session.flush()

    async def revoke_all_for_screen(self, screen_id: UUID, *, at: datetime) -> None:
        await self.session.execute(
            update(ScreenAdminSessionModel)
            .where(
                ScreenAdminSessionModel.screen_id == screen_id,
                ScreenAdminSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=at)
        )
        await self.session.flush()


__all__ = ["SqlAlchemyScreenAdminSessionRepository"]
