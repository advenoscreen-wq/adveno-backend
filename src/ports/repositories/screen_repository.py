from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    Screen,
)


class ScreenRepository(Protocol):
    async def get_by_id(self, screen_id: UUID, *, user_id: UUID | None = None) -> Screen | None: ...

    async def get_by_screen_code(
        self, screen_code: str, *, user_id: UUID | None = None
    ) -> Screen | None: ...

    async def list_all(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[Screen]: ...

    async def list_by_user_id(
        self, user_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[Screen]: ...

    async def save(self, screen: Screen) -> Screen: ...

    async def update(self, screen: Screen) -> Screen: ...
