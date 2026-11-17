"""Integration tests for assigning playlists to screens."""

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
from domain import Playlist, Screen, User
from drivers.database.models.screen_sync_state import ScreenSyncStateModel

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_assign_playlist_replaces_active_assignment_and_requests_sync(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Lobby screen")
    )
    playlist_repository = SqlAlchemyPlaylistRepository(integration_session)
    first_playlist = await playlist_repository.save(Playlist(name="First", user_id=USER_ID))
    second_playlist = await playlist_repository.save(Playlist(name="Second", user_id=USER_ID))
    await integration_session.commit()

    first_response = await client.put(
        f"/api/v1/screens/{screen.id}/playlist",
        headers=AUTH_HEADERS,
        json={"playlist_id": str(first_playlist.id)},
    )
    second_response = await client.put(
        f"/api/v1/screens/{screen.id}/playlist",
        headers=AUTH_HEADERS,
        json={"playlist_id": str(second_playlist.id)},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assignments = await SqlAlchemyScreenPlaylistAssignmentRepository(
        integration_session
    ).list_by_screen_id(screen.id)
    assert len(assignments) == 2
    assert assignments[0].unassigned_at is not None
    assert assignments[1].unassigned_at is None
    assert assignments[1].playlist_id == second_playlist.id
    sync_state = await integration_session.get(ScreenSyncStateModel, screen.id)
    assert sync_state is not None
    assert sync_state.desired_revision == 2


async def test_assign_same_playlist_is_idempotent(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Lobby screen")
    )
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Playlist", user_id=USER_ID)
    )
    await integration_session.commit()

    for _ in range(2):
        response = await client.put(
            f"/api/v1/screens/{screen.id}/playlist",
            headers=AUTH_HEADERS,
            json={"playlist_id": str(playlist.id)},
        )
        assert response.status_code == 200

    assignments = await SqlAlchemyScreenPlaylistAssignmentRepository(
        integration_session
    ).list_by_screen_id(screen.id)
    assert len(assignments) == 1
    sync_state = await integration_session.get(ScreenSyncStateModel, screen.id)
    assert sync_state is not None
    assert sync_state.desired_revision == 1


async def test_assign_playlist_returns_not_found_for_unknown_screen_or_unowned_playlist(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Lobby screen")
    )
    other_user_id = UUID("00000000-0000-0000-0000-000000000098")
    await SqlAlchemyUserRepository(integration_session).save(User(id=other_user_id))
    other_playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Private", user_id=other_user_id)
    )
    await integration_session.commit()

    for screen_id, playlist_id, expected_code in (
        (uuid4(), other_playlist.id, "SCREEN_NOT_FOUND"),
        (screen.id, other_playlist.id, "PLAYLIST_NOT_FOUND"),
    ):
        response = await client.put(
            f"/api/v1/screens/{screen_id}/playlist",
            headers=AUTH_HEADERS,
            json={"playlist_id": str(playlist_id)},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == expected_code


async def test_assign_playlist_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.put(
        f"/api/v1/screens/{uuid4()}/playlist",
        json={"playlist_id": str(uuid4())},
    )

    assert response.status_code == 401
