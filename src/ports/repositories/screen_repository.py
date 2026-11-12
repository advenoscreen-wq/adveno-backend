from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    Screen,
)


class ScreenRepository(Protocol):
    async def get_by_id(self, screen_id: UUID) -> Screen | None: ...

    async def get_by_screen_code(self, screen_code: str) -> Screen | None: ...

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[Screen]: ...

    async def save(self, screen: Screen) -> Screen: ...

    async def update(self, screen: Screen) -> Screen: ...
