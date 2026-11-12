from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError


@dataclass
class PlaylistItem:
    """Media entry and playback position inside a playlist."""

    playlist_id: UUID
    media_asset_id: UUID
    position: int
    duration_seconds: int | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.position <= 0:
            raise DomainError("playlist item position must be positive")
        if self.duration_seconds is not None and self.duration_seconds <= 0:
            raise DomainError("playlist item duration must be positive")
        validate_timestamp(self.created_at)

    def update_position(self, position: int) -> None:
        if position <= 0:
            raise DomainError("playlist item position must be positive")
        self.position = position

    def update_duration(self, duration_seconds: int | None) -> None:
        if duration_seconds is not None and duration_seconds <= 0:
            raise DomainError("playlist item duration must be positive")
        self.duration_seconds = duration_seconds
