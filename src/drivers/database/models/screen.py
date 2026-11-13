"""Persistence model for screens."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.audit_log import AuditLogModel
    from drivers.database.models.screen_credential import ScreenCredentialModel
    from drivers.database.models.screen_pairing_session import ScreenPairingSessionModel
    from drivers.database.models.screen_playlist_assignment import (
        ScreenPlaylistAssignmentModel,
    )
    from drivers.database.models.screen_sync_state import ScreenSyncStateModel


class ScreenModel(Base):
    __tablename__ = "screens"
    __table_args__ = (
        UniqueConstraint("screen_code", name="uq_screens_screen_code"),
        CheckConstraint("length(trim(screen_code)) > 0", name="ck_screens_screen_code"),
        CheckConstraint("length(trim(name)) > 0", name="ck_screens_name"),
        Index("ix_screens_status", "status"),
        Index("ix_screens_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
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
        "ScreenPairingSessionModel", back_populates="screen", lazy="raise"
    )
    credentials: Mapped[list[ScreenCredentialModel]] = relationship(
        "ScreenCredentialModel", back_populates="screen", lazy="raise"
    )
    assignments: Mapped[list[ScreenPlaylistAssignmentModel]] = relationship(
        "ScreenPlaylistAssignmentModel", back_populates="screen", lazy="raise"
    )
    sync_state: Mapped[ScreenSyncStateModel | None] = relationship(
        "ScreenSyncStateModel", back_populates="screen", uselist=False, lazy="raise"
    )
    audit_logs: Mapped[list[AuditLogModel]] = relationship(
        "AuditLogModel", back_populates="screen", lazy="raise"
    )

__all__ = ["ScreenModel"]
