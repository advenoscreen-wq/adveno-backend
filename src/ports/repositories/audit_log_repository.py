from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    AuditLog,
)


class AuditLogRepository(Protocol):
    async def list_by_screen_id(
        self, screen_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[AuditLog]: ...

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[AuditLog]: ...

    async def save(self, log: AuditLog) -> AuditLog: ...
