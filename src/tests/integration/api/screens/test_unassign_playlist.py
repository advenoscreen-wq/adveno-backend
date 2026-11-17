"""Integration tests for removing playlist assignments from screens."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyPlaylistRepository,
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
)
from domain import Playlist, Screen, ScreenPlaylistAssignment
from drivers.database.models.screen_sync_state import ScreenSyncStateModel

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_unassign_playlist_preserves_history_and_requests_screen_sync(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Assigned screen")
    )
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Assigned playlist", user_id=USER_ID)
    )
    assignment_repository = SqlAlchemyScreenPlaylistAssignmentRepository(integration_session)
    assignment = await assignment_repository.save(
        ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
    )
    await integration_session.commit()

    response = await client.delete(
        f"/api/v1/screens/{screen.id}/playlist",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 204
    assignments = await assignment_repository.list_by_screen_id(screen.id)
    assert len(assignments) == 1
    assert assignments[0].id == assignment.id
    assert assignments[0].unassigned_at is not None
    sync_state = await integration_session.get(ScreenSyncStateModel, screen.id)
    assert sync_state is not None
    assert sync_state.desired_revision == 1

    screen_response = await client.get(
        f"/api/v1/screens/{screen.id}",
        headers=AUTH_HEADERS,
    )
    assert screen_response.status_code == 200
    assert screen_response.json()["assigned_playlist"] is None


async def test_unassign_playlist_is_idempotent_when_no_playlist_is_assigned(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Unassigned screen")
    )
    await integration_session.commit()

    response = await client.delete(
        f"/api/v1/screens/{screen.id}/playlist",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 204
    assert await integration_session.get(ScreenSyncStateModel, screen.id) is None


async def test_unassign_playlist_returns_not_found_for_unknown_screen(
    client: httpx.AsyncClient,
) -> None:
    response = await client.delete(
        f"/api/v1/screens/{uuid4()}/playlist",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCREEN_NOT_FOUND"


async def test_unassign_playlist_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.delete(f"/api/v1/screens/{uuid4()}/playlist")

    assert response.status_code == 401
