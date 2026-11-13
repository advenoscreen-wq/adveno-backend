"""Backward-compatible alias for the unified user repository."""

from ports.repositories.user_repository import UserRepository

AdminProfileRepository = UserRepository

__all__ = ["AdminProfileRepository"]
