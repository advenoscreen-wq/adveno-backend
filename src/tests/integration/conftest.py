"""PostgreSQL Testcontainers configuration."""

from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from drivers.database.models.entities import Base


@pytest.fixture
def integration_database_url() -> str:
    """Return the configured integration database URL."""
    return "postgresql+asyncpg://adveno:adveno_dev_password@localhost:5432/adveno"


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
