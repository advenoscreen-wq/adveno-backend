"""SQLAlchemy persistence models for the Adveno domain."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base metadata for application persistence models."""


Timestamp = DateTime(timezone=True)
UUIDColumn = PostgreSQLUUID(as_uuid=True)


class AdminProfileModel(Base):
    __tablename__ = "admin_profiles"

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    audit_logs: Mapped[list[AuditLogModel]] = relationship(back_populates="admin", lazy="raise")


class ScreenModel(Base):
    __tablename__ = "screens"
    __table_args__ = (
        UniqueConstraint("screen_code", name="uq_screens_screen_code"),
        CheckConstraint("length(trim(screen_code)) > 0", name="ck_screens_screen_code"),
        CheckConstraint("length(trim(name)) > 0", name="ck_screens_name"),
        Index("ix_screens_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    screen_code: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_model: Mapped[str | None] = mapped_column(String(255))
    app_version: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    last_seen_at: Mapped[datetime | None] = mapped_column(Timestamp)
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(Timestamp)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    pairing_sessions: Mapped[list[ScreenPairingSessionModel]] = relationship(
        back_populates="screen", lazy="raise"
    )
    credentials: Mapped[list[ScreenCredentialModel]] = relationship(
        back_populates="screen", lazy="raise"
    )
    assignments: Mapped[list[ScreenPlaylistAssignmentModel]] = relationship(
        back_populates="screen", lazy="raise"
    )
    sync_state: Mapped[ScreenSyncStateModel | None] = relationship(
        back_populates="screen", uselist=False, lazy="raise"
    )
    audit_logs: Mapped[list[AuditLogModel]] = relationship(back_populates="screen", lazy="raise")


class ScreenPairingSessionModel(Base):
    __tablename__ = "screen_pairing_sessions"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_pairing_sessions_token_hash"),
        Index("ix_pairing_sessions_valid", "token_hash", "expires_at", "paired_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    screen_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("screens.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    paired_at: Mapped[datetime | None] = mapped_column(Timestamp)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    screen: Mapped[ScreenModel] = relationship(back_populates="pairing_sessions", lazy="raise")


class ScreenCredentialModel(Base):
    __tablename__ = "screen_credentials"
    __table_args__ = (
        Index("ix_screen_credentials_screen_id", "screen_id"),
        Index("ix_screen_credentials_active", "screen_id", "revoked_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    screen_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("screens.id", ondelete="CASCADE"), nullable=False
    )
    credential_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(Timestamp)
    revoked_at: Mapped[datetime | None] = mapped_column(Timestamp)
    screen: Mapped[ScreenModel] = relationship(back_populates="credentials", lazy="raise")


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
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
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
        back_populates="media_asset", lazy="raise"
    )


class PlaylistModel(Base):
    __tablename__ = "playlists"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_playlists_name"),
        CheckConstraint("version > 0", name="ck_playlists_version"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    items: Mapped[list[PlaylistItemModel]] = relationship(back_populates="playlist", lazy="raise")
    assignments: Mapped[list[ScreenPlaylistAssignmentModel]] = relationship(
        back_populates="playlist", lazy="raise"
    )


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
    playlist: Mapped[PlaylistModel] = relationship(back_populates="items", lazy="raise")
    media_asset: Mapped[MediaAssetModel] = relationship(
        back_populates="playlist_items", lazy="raise"
    )


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
    screen: Mapped[ScreenModel] = relationship(back_populates="assignments", lazy="raise")
    playlist: Mapped[PlaylistModel] = relationship(back_populates="assignments", lazy="raise")


class ScreenSyncStateModel(Base):
    __tablename__ = "screen_sync_states"
    __table_args__ = (
        CheckConstraint("desired_revision >= 0", name="ck_sync_states_desired_revision"),
        CheckConstraint("applied_revision >= 0", name="ck_sync_states_applied_revision"),
        CheckConstraint(
            "applied_revision <= desired_revision",
            name="ck_sync_states_revision_order",
        ),
        Index("ix_sync_states_status", "sync_status"),
    )

    screen_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("screens.id", ondelete="CASCADE"), primary_key=True
    )
    desired_revision: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    applied_revision: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    last_sync_started_at: Mapped[datetime | None] = mapped_column(Timestamp)
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(Timestamp)
    last_error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    screen: Mapped[ScreenModel] = relationship(back_populates="sync_state", lazy="raise")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_screen_id_created_at", "screen_id", "created_at"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    admin_id: Mapped[UUID | None] = mapped_column(
        UUIDColumn, ForeignKey("admin_profiles.id", ondelete="SET NULL")
    )
    screen_id: Mapped[UUID | None] = mapped_column(
        UUIDColumn, ForeignKey("screens.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    admin: Mapped[AdminProfileModel | None] = relationship(
        back_populates="audit_logs", lazy="raise"
    )
    screen: Mapped[ScreenModel | None] = relationship(back_populates="audit_logs", lazy="raise")
