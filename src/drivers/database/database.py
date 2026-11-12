"""Async SQLAlchemy engine and session configuration."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import Settings


def create_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory from application settings."""
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def check_database(session_factory: async_sessionmaker[AsyncSession]) -> bool:
    """Return whether the database accepts a simple connection."""
    try:
        async with session_factory() as session:
            await session.connection()
        return True
    except Exception:
        return False


async def session_dependency(
    request: Request,
) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped database session."""
    session = getattr(request.state, "db_session", None)
    if not isinstance(session, AsyncSession):
        raise RuntimeError("database transaction middleware is not configured")
    yield session
