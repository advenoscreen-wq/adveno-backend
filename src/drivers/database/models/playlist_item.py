"""Persistence model for playlist items."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.media_asset import MediaAssetModel
    from drivers.database.models.playlist import PlaylistModel


class PlaylistItemModel(Base):
    __tablename__ = "playlist_items"
    __table_args__ = (
        UniqueConstraint("playlist_id", "position", name="uq_playlist_items_position"),
        CheckConstraint("position > 0", name="ck_playlist_items_position"),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_playlist_items_duration",
        ),
        Index("ix_playlist_items_playlist_id", "playlist_id"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    playlist_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False
    )
    media_asset_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("media_assets.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    playlist: Mapped[PlaylistModel] = relationship(
        "PlaylistModel", back_populates="items", lazy="raise"
    )
    media_asset: Mapped[MediaAssetModel] = relationship(
        "MediaAssetModel", back_populates="playlist_items", lazy="raise"
    )


__all__ = ["PlaylistItemModel"]
