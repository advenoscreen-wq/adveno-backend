"""Persistence model for screen playlist assignments."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.playlist import PlaylistModel
    from drivers.database.models.screen import ScreenModel


class ScreenPlaylistAssignmentModel(Base):
    __tablename__ = "screen_playlist_assignments"
    __table_args__ = (
        Index(
            "uq_active_assignment_per_screen",
            "screen_id",
            unique=True,
            postgresql_where=text("unassigned_at IS NULL"),
        ),
        Index("ix_assignments_screen_id", "screen_id"),
        Index("ix_assignments_playlist_id", "playlist_id"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    screen_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("screens.id", ondelete="CASCADE"), nullable=False
    )
    playlist_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("playlists.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    unassigned_at: Mapped[datetime | None] = mapped_column(Timestamp)
    screen: Mapped[ScreenModel] = relationship(
        "ScreenModel", back_populates="assignments", lazy="raise"
    )
    playlist: Mapped[PlaylistModel] = relationship(
        "PlaylistModel", back_populates="assignments", lazy="raise"
    )


__all__ = ["ScreenPlaylistAssignmentModel"]
