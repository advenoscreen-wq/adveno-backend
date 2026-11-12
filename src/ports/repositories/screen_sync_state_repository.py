from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    ScreenSyncState,
)


class ScreenSyncStateRepository(Protocol):
    async def get_by_screen_id(self, screen_id: UUID) -> ScreenSyncState | None: ...

    async def save(self, state: ScreenSyncState) -> ScreenSyncState: ...

    async def update(self, state: ScreenSyncState) -> ScreenSyncState: ...
