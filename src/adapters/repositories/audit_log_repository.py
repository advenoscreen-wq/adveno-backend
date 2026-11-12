"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session
from adapters.repositories.mappers import (
    to_audit_log,
)
from domain.entities.entities import (
    AuditLog,
)
from drivers.database.models.entities import (
    AuditLogModel,
)


class SqlAlchemyAuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_screen_id(
        self, screen_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[AuditLog]:
        result = await self.session.scalars(
            select(AuditLogModel)
            .where(AuditLogModel.screen_id == screen_id)
            .order_by(AuditLogModel.created_at)
            .offset(offset)
            .limit(limit)
        )
        return [to_audit_log(model) for model in result]

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[AuditLog]:
        result = await self.session.scalars(
            select(AuditLogModel).order_by(AuditLogModel.created_at).offset(offset).limit(limit)
        )
        return [to_audit_log(model) for model in result]

    async def save(self, log: AuditLog) -> AuditLog:
        model = AuditLogModel(
            id=log.id,
            admin_id=log.admin_id,
            screen_id=log.screen_id,
            action=log.action,
            details=log.details,
            created_at=log.created_at,
        )
        self.session.add(model)
        await flush_session(self.session, "audit log save")
        return to_audit_log(model)
