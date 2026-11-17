"""Unit tests for user role and activation behavior."""

from typing import cast
from uuid import uuid4

import pytest

from domain import User
from domain.exceptions import DomainError
from domain.value_object import UserRole


def test_user_accepts_supported_roles() -> None:
    admin = User(id=uuid4(), role=UserRole.ADMIN)
    regular_user = User(id=uuid4(), role=UserRole.USER)

    assert admin.role is UserRole.ADMIN
    assert regular_user.role is UserRole.USER


def test_user_can_be_deactivated_and_reactivated() -> None:
    user = User(id=uuid4())

    user.deactivate()
    assert not user.is_active

    user.activate()
    assert user.is_active


def test_user_rejects_unsupported_role() -> None:
    with pytest.raises(DomainError, match="role must be ADMIN or USER"):
        User(id=uuid4(), role=cast(UserRole, "OWNER"))
