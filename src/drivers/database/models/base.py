"""Shared SQLAlchemy model infrastructure."""

from sqlalchemy import Column, DateTime, Table
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base metadata for application persistence models."""


Timestamp = DateTime(timezone=True)
UUIDColumn = PostgreSQLUUID(as_uuid=True)
AuthUsersTable = Table(
    "users",
    Base.metadata,
    Column("id", UUIDColumn, primary_key=True),
    schema="auth",
)