"""Integration tests for retrieving screens and their active playlist."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyPlaylistRepository,
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
)
from adapters.repositories.user_repository import SqlAlchemyUserRepository
from domain import Playlist, Screen, ScreenPlaylistAssignment, User

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000098")


async def test_get_screen_returns_null_assigned_playlist_when_unassigned(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Unassigned screen")
    )
    await integration_session.commit()

    response = await client.get(f"/api/v1/screens/{screen.id}", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["id"] == str(screen.id)
    assert response.json()["assigned_playlist"] is None


async def test_get_screen_returns_active_assigned_playlist(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Assigned screen")
    )
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Lobby playlist", user_id=USER_ID, description="Lobby content")
    )
    await SqlAlchemyScreenPlaylistAssignmentRepository(integration_session).save(
        ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
    )
    await integration_session.commit()

    response = await client.get(f"/api/v1/screens/{screen.id}", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["assigned_playlist"]["id"] == str(playlist.id)
    assert response.json()["assigned_playlist"]["name"] == "Lobby playlist"


async def test_get_screen_returns_not_found_for_unknown_or_unowned_screen(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    await SqlAlchemyUserRepository(integration_session).save(User(id=OTHER_USER_ID))
    other_screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=OTHER_USER_ID, name="Private screen")
    )
    await integration_session.commit()

    for screen_id in (uuid4(), other_screen.id):
        response = await client.get(f"/api/v1/screens/{screen_id}", headers=AUTH_HEADERS)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "SCREEN_NOT_FOUND"


async def test_get_screen_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.get(f"/api/v1/screens/{uuid4()}")

    assert response.status_code == 401
