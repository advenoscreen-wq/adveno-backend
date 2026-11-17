from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    ScreenPlaylistAssignment,
)


class ScreenPlaylistAssignmentRepository(Protocol):
    async def get_active_by_screen_id(self, screen_id: UUID) -> ScreenPlaylistAssignment | None: ...

    async def list_by_screen_id(
        self, screen_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[ScreenPlaylistAssignment]: ...

    async def list_by_playlist_id(
        self, playlist_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[ScreenPlaylistAssignment]: ...

    async def list_active_by_playlist_ids(
        self, playlist_ids: list[UUID]
    ) -> list[ScreenPlaylistAssignment]: ...

    async def save(self, assignment: ScreenPlaylistAssignment) -> ScreenPlaylistAssignment: ...

    async def update(self, assignment: ScreenPlaylistAssignment) -> ScreenPlaylistAssignment: ...
