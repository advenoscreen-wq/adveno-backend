from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import InvalidStateTransition


@dataclass
class ScreenPlaylistAssignment:
    """Historical assignment of a playlist to a screen."""

    screen_id: UUID
    playlist_id: UUID
    assigned_at: datetime = field(default_factory=utc_now)
    id: UUID = field(default_factory=uuid4)
    unassigned_at: datetime | None = None

    def __post_init__(self) -> None:
        validate_timestamp(self.assigned_at)
        if self.unassigned_at is not None:
            validate_timestamp(self.unassigned_at)

    def is_active(self) -> bool:
        return self.unassigned_at is None

    def unassign(self, *, at: datetime | None = None) -> None:
        if not self.is_active():
            raise InvalidStateTransition("assignment is already inactive")
        self.unassigned_at = at or utc_now()
