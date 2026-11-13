from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.entities.media_asset import MediaAsset
from domain.entities.playlist_item import PlaylistItem
from domain.exceptions import DomainError


@dataclass
class Playlist:
    """Ordered collection of active media assets."""

    name: str
    user_id: UUID
    description: str | None = None
    version: int = 1
    id: UUID = field(default_factory=uuid4)
    items: list[PlaylistItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainError("playlist name is required")
        if self.version <= 0:
            raise DomainError("playlist version must be positive")
        validate_timestamp(self.created_at)
        validate_timestamp(self.updated_at)
        self._validate_positions()

    def rename(self, name: str) -> None:
        if not name.strip():
            raise DomainError("playlist name is required")
        self.name = name
        self.updated_at = utc_now()

    def update_description(self, description: str | None) -> None:
        self.description = description
        self.updated_at = utc_now()

    def increment_version(self) -> None:
        self.version += 1
        self.updated_at = utc_now()

    def add_item(self, item: PlaylistItem, media: MediaAsset) -> None:
        if item.playlist_id != self.id:
            raise DomainError("playlist item belongs to a different playlist")
        if media.user_id != self.user_id:
            raise DomainError("media asset belongs to a different user")
        media.validate_playlist_compatibility()
        if any(existing.position == item.position for existing in self.items):
            raise DomainError("playlist item position must be unique")
        self.items.append(item)
        self.items.sort(key=lambda current: current.position)
        self.increment_version()

    def remove_item(self, item_id: UUID) -> PlaylistItem:
        for index, item in enumerate(self.items):
            if item.id == item_id:
                removed = self.items.pop(index)
                self.increment_version()
                return removed
        raise DomainError("playlist item was not found")

    def reorder_items(self, ordered_item_ids: list[UUID]) -> None:
        if len(ordered_item_ids) != len(self.items) or {item.id for item in self.items} != set(
            ordered_item_ids
        ):
            raise DomainError("reorder must include every playlist item exactly once")
        items_by_id = {item.id: item for item in self.items}
        for position, item_id in enumerate(ordered_item_ids, start=1):
            items_by_id[item_id].update_position(position)
        self.items = [items_by_id[item_id] for item_id in ordered_item_ids]
        self.increment_version()

    def _validate_positions(self) -> None:
        positions = [item.position for item in self.items]
        if len(positions) != len(set(positions)):
            raise DomainError("playlist item positions must be unique")
