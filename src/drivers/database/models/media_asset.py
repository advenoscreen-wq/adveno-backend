"""Persistence model for media assets."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.playlist_item import PlaylistItemModel


class MediaAssetModel(Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        UniqueConstraint("storage_path", name="uq_media_assets_storage_path"),
        CheckConstraint("file_size >= 0", name="ck_media_assets_file_size"),
        CheckConstraint("width IS NULL OR width > 0", name="ck_media_assets_width"),
        CheckConstraint("height IS NULL OR height > 0", name="ck_media_assets_height"),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_media_assets_duration",
        ),
        Index("ix_media_assets_status", "status"),
        Index("ix_media_assets_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("public.app_users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(String(255), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    playlist_items: Mapped[list[PlaylistItemModel]] = relationship(
        "PlaylistItemModel", back_populates="media_asset", lazy="raise"
    )


__all__ = ["MediaAssetModel"]
