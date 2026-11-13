"""Backward-compatible alias for the unified user repository."""

from adapters.repositories.user_repository import SqlAlchemyUserRepository

SqlAlchemyAdminProfileRepository = SqlAlchemyUserRepository

__all__ = ["SqlAlchemyAdminProfileRepository"]
