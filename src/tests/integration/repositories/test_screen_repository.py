"""PostgreSQL integration tests for screen persistence."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import SqlAlchemyScreenRepository
from domain.entities.entities import Screen


@pytest.mark.integration
async def test_screen_repository_round_trips_domain_entity(
    integration_session: AsyncSession,
) -> None:
    repository = SqlAlchemyScreenRepository(integration_session)
    screen = Screen(screen_code="SCR-1", name="Lobby")

    await repository.save(screen)
    loaded = await repository.get_by_screen_code("SCR-1")

    assert loaded is not None
    assert loaded.id == screen.id
    assert loaded.name == "Lobby"
