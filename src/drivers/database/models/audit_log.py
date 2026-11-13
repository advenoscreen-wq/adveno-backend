"""Persistence model for audit logs."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.screen import ScreenModel
    from drivers.database.models.user import UserModel


class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_screen_id_created_at", "screen_id", "created_at"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(UUIDColumn, primary_key=True, default=uuid4)
    admin_id: Mapped[UUID | None] = mapped_column(
        UUIDColumn, ForeignKey("users.id", ondelete="SET NULL")
    )
    screen_id: Mapped[UUID | None] = mapped_column(
        UUIDColumn, ForeignKey("screens.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    admin: Mapped[UserModel | None] = relationship(
        "UserModel", back_populates="audit_logs", lazy="raise"
    )
    screen: Mapped[ScreenModel | None] = relationship(
        "ScreenModel", back_populates="audit_logs", lazy="raise"
    )


__all__ = ["AuditLogModel"]
