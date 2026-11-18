"""Integration tests for deleting a screen."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyPlaylistRepository,
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
)
from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from domain import Playlist, Screen, ScreenCredential, ScreenPlaylistAssignment

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_delete_screen_removes_screen_credentials_and_assignments(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Screen to delete")
    )
    credential = await SqlAlchemyScreenCredentialRepository(integration_session).save(
        ScreenCredential(screen_id=screen.id, credential_hash=uuid4().hex)
    )
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Assigned playlist", user_id=USER_ID)
    )
    assignment_repository = SqlAlchemyScreenPlaylistAssignmentRepository(integration_session)
    await assignment_repository.save(
        ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
    )
    await integration_session.commit()

    response = await client.delete(f"/api/v1/screens/{screen.id}", headers=AUTH_HEADERS)

    assert response.status_code == 204
    assert await SqlAlchemyScreenRepository(integration_session).get_by_id(screen.id) is None
    assert (
        await SqlAlchemyScreenCredentialRepository(integration_session).get_by_id(credential.id)
        is None
    )
    assert await assignment_repository.list_by_screen_id(screen.id) == []


async def test_delete_screen_returns_not_found_for_unknown_screen(
    client: httpx.AsyncClient,
) -> None:
    response = await client.delete(f"/api/v1/screens/{uuid4()}", headers=AUTH_HEADERS)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCREEN_NOT_FOUND"


async def test_delete_screen_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.delete(f"/api/v1/screens/{uuid4()}")

    assert response.status_code == 401
