"""Persistence model for screen synchronization state."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.screen import ScreenModel


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
    desired_revision: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    applied_revision: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    last_sync_started_at: Mapped[datetime | None] = mapped_column(Timestamp)
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(Timestamp)
    last_error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    screen: Mapped[ScreenModel] = relationship(
        "ScreenModel", back_populates="sync_state", lazy="raise"
    )


__all__ = ["ScreenSyncStateModel"]
