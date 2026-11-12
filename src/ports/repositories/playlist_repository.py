from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    Playlist,
)


class PlaylistRepository(Protocol):
    async def get_by_id(self, playlist_id: UUID) -> Playlist | None: ...

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[Playlist]: ...

    async def save(self, playlist: Playlist) -> Playlist: ...

    async def update(self, playlist: Playlist) -> Playlist: ...

    async def delete(self, playlist_id: UUID) -> None: ...
