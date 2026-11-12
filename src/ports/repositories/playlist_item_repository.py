from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    PlaylistItem,
)


class PlaylistItemRepository(Protocol):
    async def list_by_playlist_id(
        self, playlist_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[PlaylistItem]: ...

    async def save(self, item: PlaylistItem) -> PlaylistItem: ...

    async def update(self, item: PlaylistItem) -> PlaylistItem: ...

    async def delete(self, item_id: UUID) -> None: ...
