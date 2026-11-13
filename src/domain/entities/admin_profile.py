"""Backward-compatible alias for the unified user entity."""

from domain.entities.user import User

AdminProfile = User

__all__ = ["AdminProfile"]
