"""Shared domain entity helpers."""

from datetime import UTC, datetime

from domain.exceptions import DomainError


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def validate_timestamp(value: datetime) -> None:
    if value.tzinfo is None:
        raise DomainError("timestamps must be timezone-aware")
