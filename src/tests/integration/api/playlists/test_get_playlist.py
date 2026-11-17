"""Integration tests for retrieving a playlist."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.playlist_repository import SqlAlchemyPlaylistRepository
from adapters.repositories.user_repository import SqlAlchemyUserRepository
from domain import Playlist, User

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000098")


async def test_get_playlist_returns_owned_playlist(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    playlist = Playlist(name="Saved playlist", user_id=USER_ID, description="For lobby")
    await SqlAlchemyPlaylistRepository(integration_session).save(playlist)
    await integration_session.commit()

    response = await client.get(
        f"/api/v1/playlists/{playlist.id}",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(playlist.id)
    assert response.json()["name"] == "Saved playlist"
    assert response.json()["items"] == []


async def test_get_playlist_returns_not_found_for_missing_or_unowned_playlist(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    await SqlAlchemyUserRepository(integration_session).save(User(id=OTHER_USER_ID))
    other_user_playlist = Playlist(name="Private", user_id=OTHER_USER_ID)
    await SqlAlchemyPlaylistRepository(integration_session).save(other_user_playlist)
    await integration_session.commit()

    for playlist_id in (uuid4(), other_user_playlist.id):
        response = await client.get(
            f"/api/v1/playlists/{playlist_id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PLAYLIST_NOT_FOUND"


async def test_get_playlist_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.get(f"/api/v1/playlists/{uuid4()}")

    assert response.status_code == 401
