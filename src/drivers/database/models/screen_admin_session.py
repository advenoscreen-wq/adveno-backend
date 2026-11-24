"""Persistence model for short-lived screen administration sessions."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.screen import ScreenModel


class ScreenAdminSessionModel(Base):
    __tablename__ = "screen_admin_sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_screen_admin_sessions_expiration"),
        UniqueConstraint("token_hash", name="uq_screen_admin_sessions_token_hash"),
        Index("ix_screen_admin_sessions_screen_created", "screen_id", "created_at"),
        Index(
            "uq_screen_admin_sessions_pending_pin_per_screen",
            "screen_id",
            unique=True,
            postgresql_where=text("token_hash IS NULL AND revoked_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    screen_id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("screens.id", ondelete="CASCADE"), nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    token_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(Timestamp)
    screen: Mapped[ScreenModel] = relationship("ScreenModel", lazy="raise")


__all__ = ["ScreenAdminSessionModel"]
