"""Persistence model for immutable playback reports from screens."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from drivers.database.models.base import Base, Timestamp, UUIDColumn


class ScreenPlaybackEventModel(Base):
    __tablename__ = "screen_playback_events"
    __table_args__ = (
        UniqueConstraint("screen_id", "event_id", name="uq_playback_events_screen_event_id"),
        CheckConstraint("playlist_version > 0", name="ck_playback_events_playlist_version"),
        CheckConstraint(
            "played_complete_at IS NULL OR played_complete_at >= played_at",
            name="ck_playback_events_completion_after_start",
        ),
        Index("ix_playback_events_screen_played_at", "screen_id", "played_at"),
        Index("ix_playback_events_playlist_played_at", "playlist_id", "played_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(UUIDColumn, nullable=False)
    screen_id: Mapped[UUID] = mapped_column(UUIDColumn, nullable=False)
    playlist_id: Mapped[UUID] = mapped_column(UUIDColumn, nullable=False)
    playlist_item_id: Mapped[UUID] = mapped_column(UUIDColumn, nullable=False)
    media_asset_id: Mapped[UUID] = mapped_column(UUIDColumn, nullable=False)
    playlist_version: Mapped[int] = mapped_column(Integer, nullable=False)
    media_checksum: Mapped[str] = mapped_column(String(255), nullable=False)
    played_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    played_complete_at: Mapped[datetime | None] = mapped_column(Timestamp)
    received_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )


__all__ = ["ScreenPlaybackEventModel"]
