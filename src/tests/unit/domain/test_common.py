"""Unit tests for shared domain timestamp helpers."""

from datetime import UTC, datetime

import pytest

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError


def test_utc_now_returns_timezone_aware_utc_datetime() -> None:
    current_time = utc_now()

    assert current_time.tzinfo is UTC


def test_validate_timestamp_rejects_naive_datetime() -> None:
    with pytest.raises(DomainError, match="timestamps must be timezone-aware"):
        validate_timestamp(datetime(2026, 1, 1))


def test_validate_timestamp_accepts_aware_datetime() -> None:
    validate_timestamp(datetime(2026, 1, 1, tzinfo=UTC))
