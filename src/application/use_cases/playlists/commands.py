"""Commands for playlist use cases."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreatePlaylistItemCommand:
    media_asset_id: UUID
    position: int
    duration_seconds: int | None = None


@dataclass(frozen=True)
class CreatePlaylistCommand:
    user_id: UUID
    name: str
    description: str | None
    items: list[CreatePlaylistItemCommand]


@dataclass(frozen=True)
class UpdatePlaylistCommand:
    playlist_id: UUID
    user_id: UUID
    name: str
    description: str | None
    items: list[CreatePlaylistItemCommand]
