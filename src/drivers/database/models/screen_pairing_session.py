"""Persistence model for screen pairing sessions."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.screen import ScreenModel


class ScreenPairingSessionModel(Base):
    __tablename__ = "screen_pairing_sessions"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_pairing_sessions_token_hash"),
        CheckConstraint(
            "pairing_type IS NULL OR pairing_type IN ('NEW_SCREEN', 'RECONNECT_EXISTING')",
            name="ck_pairing_sessions_pairing_type",
        ),
        CheckConstraint(
            "(pairing_type IS NULL AND screen_id IS NULL AND paired_at IS NULL "
            "AND status IN ('PENDING', 'EXPIRED')) OR "
            "(pairing_type = 'NEW_SCREEN' AND "
            "((paired_at IS NULL AND screen_id IS NULL "
            "AND status IN ('PENDING', 'CONNECTING', 'EXPIRED')) OR "
            "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED'))) OR "
            "(pairing_type = 'RECONNECT_EXISTING' AND "
            "((paired_at IS NULL AND screen_id IS NULL AND status IN ('PENDING', 'EXPIRED')) OR "
            "(paired_at IS NULL AND screen_id IS NOT NULL AND status = 'CONNECTING') OR "
            "(paired_at IS NOT NULL AND screen_id IS NOT NULL AND status = 'PAIRED')))",
            name="ck_pairing_sessions_screen_reference",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'CONNECTING', 'PAIRED', 'EXPIRED')",
            name="ck_pairing_sessions_status",
        ),
        Index("ix_pairing_sessions_valid", "token_hash", "expires_at", "paired_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    screen_id: Mapped[UUID | None] = mapped_column(
        UUIDColumn, ForeignKey("screens.id", ondelete="CASCADE"), nullable=True
    )
    pairing_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    paired_at: Mapped[datetime | None] = mapped_column(Timestamp)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    screen: Mapped[ScreenModel | None] = relationship(
        "ScreenModel", back_populates="pairing_sessions", lazy="raise"
    )


__all__ = ["ScreenPairingSessionModel"]
