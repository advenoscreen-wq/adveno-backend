"""A screen-reported ad playback event."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.entities.common import validate_timestamp
from domain.exceptions import DomainError


@dataclass(frozen=True)
class ScreenPlaybackEvent:
    screen_id: UUID
    event_id: UUID
    playlist_id: UUID
    playlist_item_id: UUID
    media_asset_id: UUID
    playlist_version: int
    media_checksum: str
    played_at: datetime
    played_complete_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.playlist_version < 1:
            raise DomainError("playlist version must be positive")
        if not self.media_checksum.strip():
            raise DomainError("media checksum is required")
        validate_timestamp(self.played_at)
        if self.played_complete_at is not None:
            validate_timestamp(self.played_complete_at)
        if self.played_complete_at is not None and self.played_complete_at < self.played_at:
            raise DomainError("playback completion cannot precede playback start")


__all__ = ["ScreenPlaybackEvent"]
