"""Integration tests for deleting playlists and their screen assignments."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyPlaylistItemRepository,
    SqlAlchemyPlaylistRepository,
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
)
from domain import Playlist, Screen, ScreenPlaylistAssignment
from drivers.database.models.screen_sync_state import ScreenSyncStateModel

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_delete_playlist_removes_items_and_all_assignments_and_syncs_screen(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="To delete", user_id=USER_ID)
    )
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Assigned screen")
    )
    assignments = SqlAlchemyScreenPlaylistAssignmentRepository(integration_session)
    await assignments.save(ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id))
    await assignments.save(
        ScreenPlaylistAssignment(
            screen_id=screen.id,
            playlist_id=playlist.id,
            unassigned_at=screen.created_at,
        )
    )
    await integration_session.commit()

    response = await client.delete(
        f"/api/v1/playlists/{playlist.id}",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 204
    assert response.content == b""
    assert (
        await SqlAlchemyPlaylistRepository(integration_session).get_by_id(
            playlist.id,
            user_id=USER_ID,
        )
        is None
    )
    assert await assignments.list_by_playlist_id(playlist.id) == []
    assert (
        await SqlAlchemyPlaylistItemRepository(integration_session).list_by_playlist_id(playlist.id)
        == []
    )
    sync_state = await integration_session.get(ScreenSyncStateModel, screen.id)
    assert sync_state is not None
    assert sync_state.desired_revision == 1


async def test_delete_playlist_returns_not_found_for_unknown_or_unowned_playlist(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    other_user_playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Private", user_id=uuid4())
    )
    await integration_session.commit()

    for playlist_id in (uuid4(), other_user_playlist.id):
        response = await client.delete(
            f"/api/v1/playlists/{playlist_id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PLAYLIST_NOT_FOUND"


async def test_delete_playlist_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.delete(f"/api/v1/playlists/{uuid4()}")

    assert response.status_code == 401
