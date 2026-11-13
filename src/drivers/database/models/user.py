"""Persistence model for users."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drivers.database.models.base import Base, Timestamp, UUIDColumn

if TYPE_CHECKING:
    from drivers.database.models.audit_log import AuditLogModel


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'USER')", name="ck_users_role"),
        Index("ix_users_role", "role"),
    )

    id: Mapped[UUID] = mapped_column(
        UUIDColumn, ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, nullable=False, server_default=func.now()
    )
    audit_logs: Mapped[list[AuditLogModel]] = relationship(
        "AuditLogModel", back_populates="admin", lazy="raise"
    )

__all__ = ["UserModel"]
