from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def save(self, user: User) -> User: ...

    async def update(self, user: User) -> User: ...
