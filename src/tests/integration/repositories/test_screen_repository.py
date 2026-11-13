"""PostgreSQL integration tests for screen persistence."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyScreenRepository,
    SqlAlchemyUserRepository,
)
from domain import Screen, User


@pytest.mark.integration
async def test_screen_repository_round_trips_domain_entity(
    integration_session: AsyncSession,
) -> None:
    repository = SqlAlchemyScreenRepository(integration_session)
    user = User(id=uuid4())
    await integration_session.execute(
        text("INSERT INTO auth.users (id) VALUES (:id)"), {"id": user.id}
    )
    await SqlAlchemyUserRepository(integration_session).save(user)
    screen = Screen(user_id=user.id, screen_code="SCR-1", name="Lobby")

    await repository.save(screen)
    loaded = await repository.get_by_screen_code("SCR-1")

    assert loaded is not None
    assert loaded.id == screen.id
    assert loaded.name == "Lobby"
