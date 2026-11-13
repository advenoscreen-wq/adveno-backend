from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session
from domain import User, UserRole
from domain.exceptions import PersistenceError
from drivers.database.models.entities import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self.session.get(UserModel, user_id)
        return (
            User(
                id=model.id,
                role=UserRole(model.role),
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            if model
            else None
        )

    async def save(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self.session.add(model)
        await flush_session(self.session, "user save")
        return user

    async def update(self, user: User) -> User:
        model = await self.session.get(UserModel, user.id)
        if model is None:
            raise PersistenceError("user was not found")
        model.role = user.role.value
        model.is_active = user.is_active
        model.updated_at = user.updated_at
        await flush_session(self.session, "user update")
        return user
