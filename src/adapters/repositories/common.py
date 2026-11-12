"""Shared repository persistence helpers."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.exceptions import PersistenceConflictError


async def flush_session(session: AsyncSession, operation: str) -> None:
    """Flush a repository transaction and translate integrity conflicts."""
    try:
        await session.flush()
    except IntegrityError as error:
        await session.rollback()
        raise PersistenceConflictError(f"{operation} violates a persistence constraint") from error
