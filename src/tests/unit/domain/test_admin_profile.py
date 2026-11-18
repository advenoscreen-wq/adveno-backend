"""Unit tests for the legacy admin profile alias."""

from uuid import uuid4

from domain.entities.admin_profile import AdminProfile
from domain.entities.user import User


def test_admin_profile_alias_creates_a_user_entity() -> None:
    profile = AdminProfile(id=uuid4())

    assert isinstance(profile, User)
