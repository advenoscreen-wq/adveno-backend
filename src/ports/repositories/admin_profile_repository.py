from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    AdminProfile,
)


class AdminProfileRepository(Protocol):
    async def get_by_id(self, profile_id: UUID) -> AdminProfile | None: ...

    async def save(self, profile: AdminProfile) -> AdminProfile: ...

    async def update(self, profile: AdminProfile) -> AdminProfile: ...
