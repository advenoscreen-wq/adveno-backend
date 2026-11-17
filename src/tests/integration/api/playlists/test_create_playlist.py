"""Integration tests for creating playlists with selected media assets."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.media_asset_repository import SqlAlchemyMediaAssetRepository
from adapters.repositories.playlist_repository import SqlAlchemyPlaylistRepository
from domain import MediaAsset
from domain.value_object import MediaType

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def create_media(session: AsyncSession, name: str) -> MediaAsset:
    return await SqlAlchemyMediaAssetRepository(session).save(
        MediaAsset(
            user_id=USER_ID,
            name=name,
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            storage_path=f"users/{USER_ID}/{uuid4().hex}/{name}.png",
            file_size=512,
            checksum=uuid4().hex,
        )
    )


async def test_create_playlist_persists_selected_media_in_order(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    first_media = await create_media(integration_session, "First")
    second_media = await create_media(integration_session, "Second")
    await integration_session.commit()

    response = await client.post(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        json={
            "name": "Lobby playlist",
            "description": "Lobby content",
            "items": [
                {
                    "media_asset_id": str(second_media.id),
                    "position": 2,
                    "duration_seconds": 15,
                },
                {"media_asset_id": str(first_media.id), "position": 1},
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Lobby playlist"
    assert body["description"] == "Lobby content"
    assert [item["media_asset_id"] for item in body["items"]] == [
        str(first_media.id),
        str(second_media.id),
    ]
    assert [item["position"] for item in body["items"]] == [1, 2]
    assert body["items"][1]["duration_seconds"] == 15

    persisted = await SqlAlchemyPlaylistRepository(integration_session).get_by_id(
        UUID(body["id"]),
        user_id=USER_ID,
    )
    assert persisted is not None
    assert len(persisted.items) == 2


async def test_create_playlist_without_items(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    response = await client.post(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        json={"name": "Empty playlist"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Empty playlist"
    assert body["items"] == []
    persisted = await SqlAlchemyPlaylistRepository(integration_session).get_by_id(
        UUID(body["id"]),
        user_id=USER_ID,
    )
    assert persisted is not None
    assert persisted.items == []


async def test_create_playlist_rejects_missing_media_before_persisting_playlist(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    media = await create_media(integration_session, "Existing")
    await integration_session.commit()

    response = await client.post(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        json={
            "name": "Invalid playlist",
            "items": [
                {"media_asset_id": str(media.id), "position": 1},
                {"media_asset_id": str(uuid4()), "position": 2},
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"
    assert await SqlAlchemyPlaylistRepository(integration_session).list_by_user_id(USER_ID) == []


async def test_create_playlist_rejects_duplicate_item_positions(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        json={
            "name": "Invalid playlist",
            "items": [
                {"media_asset_id": str(uuid4()), "position": 1},
                {"media_asset_id": str(uuid4()), "position": 1},
            ],
        },
    )

    assert response.status_code == 422


async def test_create_playlist_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/playlists",
        json={"name": "Private playlist", "items": []},
    )

    assert response.status_code == 401
