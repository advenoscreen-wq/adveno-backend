"""Unit tests for domain enum values."""

import pytest

from domain.value_object import (
    MediaStatus,
    MediaType,
    PairingSessionStatus,
    PairingType,
    ScreenStatus,
    SyncStatus,
    UserRole,
)


@pytest.mark.parametrize(
    ("value_type", "value"),
    [
        (MediaStatus, "ACTIVE"),
        (MediaType, "VIDEO"),
        (PairingSessionStatus, "PAIRED"),
        (PairingType, "NEW_SCREEN"),
        (ScreenStatus, "INACTIVE"),
        (SyncStatus, "SYNCED"),
        (UserRole, "ADMIN"),
    ],
)
def test_domain_enum_accepts_declared_string_value(value_type, value: str) -> None:
    assert value_type(value).value == value


def test_pairing_type_rejects_undeclared_value() -> None:
    with pytest.raises(ValueError):
        PairingType("UNKNOWN")
