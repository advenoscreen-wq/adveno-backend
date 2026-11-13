"""PostgreSQL Testcontainers configuration."""

from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer

from adapters.services.redis_cache_service import RedisCacheService
from drivers.database.models.entities import Base


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    """Start an isolated PostgreSQL container for repository integration tests."""
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest_asyncio.fixture
async def integration_session(
    postgres_container: PostgresContainer,
) -> AsyncIterator[AsyncSession]:
    """Create a clean schema and session for one integration test."""
    url = postgres_container.get_connection_url()
    async_url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    engine = create_async_engine(async_url)
    async with engine.begin() as connection:
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        await connection.execute(
            text("CREATE TABLE IF NOT EXISTS auth.users (id UUID PRIMARY KEY)")
        )
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def redis_container() -> Iterator[RedisContainer]:
    """Start an isolated Redis container for cache integration tests."""
    with RedisContainer("redis:7-alpine") as container:
        yield container


@pytest_asyncio.fixture
async def redis_service(redis_container: RedisContainer) -> AsyncIterator[RedisCacheService]:
    """Provide a clean Redis service and remove its data after each test."""
    redis_url = (
        f"redis://{redis_container.get_container_host_ip()}:"
        f"{redis_container.get_exposed_port(6379)}"
    )
    service = RedisCacheService(redis_url)
    try:
        yield service
    finally:
        await service.clear()
        await service.close()
