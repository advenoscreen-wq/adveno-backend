"""Persistence contract for temporary screen-admin sessions."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from domain import ScreenAdminSession


class ScreenAdminSessionRepository(Protocol):
    async def get_pending_pin_by_screen_id(
        self, screen_id: UUID, *, for_update: bool = False
    ) -> ScreenAdminSession | None: ...

    async def get_by_screen_id_and_token_hash(
        self, screen_id: UUID, token_hash: str, *, for_update: bool = False
    ) -> ScreenAdminSession | None: ...

    async def save(self, session: ScreenAdminSession) -> ScreenAdminSession: ...

    async def update(self, session: ScreenAdminSession) -> ScreenAdminSession: ...

    async def revoke_pending_by_screen_id(self, screen_id: UUID, *, at: datetime) -> None: ...

    async def revoke_all_for_screen(self, screen_id: UUID, *, at: datetime) -> None: ...
