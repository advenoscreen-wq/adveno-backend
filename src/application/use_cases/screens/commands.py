"""Commands accepted by screen use cases."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AcknowledgeScreenSyncCommand:
    applied_revision: int


@dataclass(frozen=True)
class PlaybackEventData:
    event_id: UUID
    playlist_id: UUID
    playlist_item_id: UUID
    media_asset_id: UUID
    playlist_version: int
    media_checksum: str
    played_at: datetime
    played_complete_at: datetime | None


@dataclass(frozen=True)
class ReportScreenPlaybackEventsCommand:
    events: list[PlaybackEventData]


@dataclass(frozen=True)
class VerifyScreenAdminSessionCommand:
    pin: str


@dataclass(frozen=True)
class CreateScreenAdminSessionCommand:
    screen_id: UUID
    user_id: UUID
