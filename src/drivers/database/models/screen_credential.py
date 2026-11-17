"""Persistence model for screen credentials."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.screen import ScreenModel


class ScreenCredentialModel(Base):
    __tablename__ = "screen_credentials"
    __table_args__ = (
        Index("ix_screen_credentials_screen_id", "screen_id"),
        Index(
            "uq_screen_credentials_one_active_per_screen",
            "screen_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
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
    screen: Mapped[ScreenModel] = relationship(
        "ScreenModel", back_populates="credentials", lazy="raise"
    )


__all__ = ["ScreenCredentialModel"]
