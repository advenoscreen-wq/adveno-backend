"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session, log_repository_operations
from adapters.repositories.mappers import (
    apply_credential,
    to_credential,
)
from domain.entities.entities import (
    ScreenCredential,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    ScreenCredentialModel,
)


@log_repository_operations
class SqlAlchemyScreenCredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, credential_id: UUID) -> ScreenCredential | None:
        model = await self.session.get(ScreenCredentialModel, credential_id)
        return to_credential(model) if model else None

    async def get_active_credential_by_screen(
        self, screen_id: UUID, *, for_update: bool = False
    ) -> ScreenCredential | None:
        statement = select(ScreenCredentialModel).where(
            ScreenCredentialModel.screen_id == screen_id,
            ScreenCredentialModel.revoked_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        model = await self.session.scalar(statement)
        return to_credential(model) if model else None

    async def get_active_credentials_by_screen(self, screen_id: UUID) -> list[ScreenCredential]:
        result = await self.session.scalars(
            select(ScreenCredentialModel)
            .where(
                ScreenCredentialModel.screen_id == screen_id,
                ScreenCredentialModel.revoked_at.is_(None),
            )
            .order_by(ScreenCredentialModel.created_at)
        )
        return [to_credential(model) for model in result]

    async def save(self, credential: ScreenCredential) -> ScreenCredential:
        if credential.revoked_at is None and await self.get_active_credentials_by_screen(
            credential.screen_id
        ):
            raise PersistenceError("screen already has an active credential")
        model = ScreenCredentialModel()
        apply_credential(credential, model)
        self.session.add(model)
        await flush_session(self.session, "screen credential save")
        return to_credential(model)

    async def update(self, credential: ScreenCredential) -> ScreenCredential:
        model = await self.session.get(ScreenCredentialModel, credential.id)
        if model is None:
            raise PersistenceError("screen credential was not found")
        apply_credential(credential, model)
        await flush_session(self.session, "screen credential update")
        return to_credential(model)
