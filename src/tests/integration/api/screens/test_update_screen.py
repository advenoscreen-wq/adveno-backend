"""Integration tests for user-managed screen updates."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from domain import Screen

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


async def test_update_screen_changes_name_and_preserves_device_details(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(
            user_id=USER_ID,
            screen_code="SCR-TEST-CODE-1234",
            name="Old name",
            device_model="Android TV",
            app_version="1.2.3",
        )
    )
    await integration_session.commit()

    response = await client.patch(
        f"/api/v1/screens/{screen.id}",
        headers={"Authorization": "Bearer valid-access-token"},
        json={"name": "  Lobby TV  "},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Lobby TV"
    assert body["screen_code"] == screen.screen_code
    assert body["status"] == screen.status.value

    updated = await SqlAlchemyScreenRepository(integration_session).get_by_id(screen.id)
    assert updated is not None
    assert updated.name == "Lobby TV"
    assert updated.device_model == "Android TV"
    assert updated.app_version == "1.2.3"


async def test_update_screen_returns_not_found_for_unknown_screen(
    client: httpx.AsyncClient,
) -> None:
    response = await client.patch(
        f"/api/v1/screens/{uuid4()}",
        headers={"Authorization": "Bearer valid-access-token"},
        json={"name": "Lobby TV"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCREEN_NOT_FOUND"


async def test_update_screen_rejects_blank_name(client: httpx.AsyncClient) -> None:
    response = await client.patch(
        f"/api/v1/screens/{uuid4()}",
        headers={"Authorization": "Bearer valid-access-token"},
        json={"name": "   "},
    )

    assert response.status_code == 422


async def test_update_screen_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.patch(
        f"/api/v1/screens/{uuid4()}",
        json={"name": "Lobby TV"},
    )

    assert response.status_code == 401
