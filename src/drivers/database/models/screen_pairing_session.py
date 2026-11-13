"""Persistence model for screen pairing sessions."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.screen import ScreenModel


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
    screen: Mapped[ScreenModel] = relationship(
        "ScreenModel", back_populates="pairing_sessions", lazy="raise"
    )


__all__ = ["ScreenPairingSessionModel"]
