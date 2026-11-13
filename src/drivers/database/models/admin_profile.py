"""Persistence model for admin_profile."""

from drivers.database.models.entities import UserModel

AdminProfileModel = UserModel

__all__ = ["AdminProfileModel", "UserModel"]
