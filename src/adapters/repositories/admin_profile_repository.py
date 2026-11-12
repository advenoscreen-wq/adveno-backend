"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session
from adapters.repositories.mappers import (
    apply_admin_profile,
    to_admin_profile,
)
from domain.entities.entities import (
    AdminProfile,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    AdminProfileModel,
)


class SqlAlchemyAdminProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, profile_id: UUID) -> AdminProfile | None:
        model = await self.session.get(AdminProfileModel, profile_id)
        return to_admin_profile(model) if model else None

    async def save(self, profile: AdminProfile) -> AdminProfile:
        model = AdminProfileModel()
        apply_admin_profile(profile, model)
        self.session.add(model)
        await flush_session(self.session, "admin profile save")
        return to_admin_profile(model)

    async def update(self, profile: AdminProfile) -> AdminProfile:
        model = await self.session.get(AdminProfileModel, profile.id)
        if model is None:
            raise PersistenceError("admin profile was not found")
        apply_admin_profile(profile, model)
        await flush_session(self.session, "admin profile update")
        return to_admin_profile(model)
