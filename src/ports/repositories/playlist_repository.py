from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    Playlist,
)


class PlaylistRepository(Protocol):
    async def get_by_id(
        self, playlist_id: UUID, *, user_id: UUID | None = None
    ) -> Playlist | None: ...

    async def list_all(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[Playlist]: ...

    async def list_by_user_id(
        self,
        user_id: UUID,
        *,
        filter_by_title: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Playlist]: ...

    async def count_by_user_id(
        self, user_id: UUID, *, filter_by_title: str | None = None
    ) -> int: ...

    async def save(self, playlist: Playlist) -> Playlist: ...

    async def update(self, playlist: Playlist) -> Playlist: ...

    async def increment_versions(self, playlist_ids: list[UUID]) -> None: ...

    async def delete(self, playlist_id: UUID) -> None: ...
