"""Integration tests for paginated playlist listing and filtering."""

from uuid import UUID

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


async def test_list_playlists_filters_name_and_description_for_current_user(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    repository = SqlAlchemyPlaylistRepository(integration_session)
    await repository.save(Playlist(name="Keyword name", user_id=USER_ID))
    await repository.save(
        Playlist(name="Another playlist", description="Has keyword here", user_id=USER_ID)
    )
    await repository.save(Playlist(name="Unrelated", user_id=USER_ID))
    await SqlAlchemyUserRepository(integration_session).save(User(id=OTHER_USER_ID))
    await repository.save(Playlist(name="Keyword private", user_id=OTHER_USER_ID))
    await integration_session.commit()

    response = await client.get(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        params={"filter_by_title": "keyword"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 2
    assert body["total_pages"] == 1
    assert len(body["items"]) == 2
    assert {item["name"] for item in body["items"]} == {
        "Keyword name",
        "Another playlist",
    }


async def test_list_playlists_returns_requested_page(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    repository = SqlAlchemyPlaylistRepository(integration_session)
    for index in range(3):
        await repository.save(Playlist(name=f"Playlist {index}", user_id=USER_ID))
    await integration_session.commit()
    expected_page = await repository.list_by_user_id(USER_ID, offset=2, limit=2)

    response = await client.get(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        params={"page": 2, "limit": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 3
    assert body["total_pages"] == 2
    assert body["page"] == 2
    assert body["limit"] == 2
    assert body["has_next"] is False
    assert body["has_prev"] is True
    assert [item["id"] for item in body["items"]] == [
        str(playlist.id) for playlist in expected_page
    ]


async def test_list_playlists_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/playlists")

    assert response.status_code == 401
