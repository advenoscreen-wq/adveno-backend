"""Integration tests for listing the authenticated user's screens."""

from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from adapters.repositories.user_repository import SqlAlchemyUserRepository
from domain import Screen, User

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000098")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_list_screens_returns_only_current_user_screens_with_pagination(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    repository = SqlAlchemyScreenRepository(integration_session)
    for index in range(3):
        await repository.save(Screen(user_id=USER_ID, name=f"Screen {index}"))
    await SqlAlchemyUserRepository(integration_session).save(User(id=OTHER_USER_ID))
    await repository.save(Screen(user_id=OTHER_USER_ID, name="Private screen"))
    await integration_session.commit()
    expected_page = await repository.list_by_user_id(USER_ID, offset=1, limit=1)

    response = await client.get(
        "/api/v1/screens",
        headers=AUTH_HEADERS,
        params={"page": 2, "limit": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 3
    assert body["total_pages"] == 3
    assert body["has_next"] is True
    assert body["has_prev"] is True
    assert [item["id"] for item in body["items"]] == [str(expected_page[0].id)]


async def test_list_screens_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/screens")

    assert response.status_code == 401


async def test_list_screens_filters_names_case_insensitively(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    repository = SqlAlchemyScreenRepository(integration_session)
    await repository.save(Screen(user_id=USER_ID, name="Lobby Display"))
    await repository.save(Screen(user_id=USER_ID, name="Meeting Room"))
    await integration_session.commit()

    response = await client.get(
        "/api/v1/screens",
        headers=AUTH_HEADERS,
        params={"filter_by_name": "lObBy"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert [screen["name"] for screen in body["items"]] == ["Lobby Display"]
