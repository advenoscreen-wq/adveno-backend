"""Persistence model for playlists."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.playlist_item import PlaylistItemModel
    from drivers.database.models.screen_playlist_assignment import (
        ScreenPlaylistAssignmentModel,
    )


class PlaylistModel(Base):
    __tablename__ = "playlists"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_playlists_name"),
        CheckConstraint("version > 0", name="ck_playlists_version"),
        Index("ix_playlists_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("public.app_users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    items: Mapped[list[PlaylistItemModel]] = relationship(
        "PlaylistItemModel", back_populates="playlist", lazy="raise"
    )
    assignments: Mapped[list[ScreenPlaylistAssignmentModel]] = relationship(
        "ScreenPlaylistAssignmentModel", back_populates="playlist", lazy="raise"
    )


__all__ = ["PlaylistModel"]
