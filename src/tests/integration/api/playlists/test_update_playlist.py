"""Integration tests for replacing playlist details and selected media."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyMediaAssetRepository,
    SqlAlchemyPlaylistItemRepository,
    SqlAlchemyPlaylistRepository,
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
)
from domain import MediaAsset, Playlist, PlaylistItem, Screen, ScreenPlaylistAssignment
from domain.value_object import MediaType
from drivers.database.models.screen_sync_state import ScreenSyncStateModel

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


async def test_update_playlist_replaces_items_and_increments_assigned_screen_sync(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    old_media = await create_media(integration_session, "Old")
    first_media = await create_media(integration_session, "First")
    second_media = await create_media(integration_session, "Second")
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Old playlist", user_id=USER_ID, description="Old details")
    )
    item_repository = SqlAlchemyPlaylistItemRepository(integration_session)
    await item_repository.save(
        PlaylistItem(playlist_id=playlist.id, media_asset_id=old_media.id, position=1)
    )
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Lobby screen")
    )
    await SqlAlchemyScreenPlaylistAssignmentRepository(integration_session).save(
        ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
    )
    await integration_session.commit()

    response = await client.put(
        f"/api/v1/playlists/{playlist.id}",
        headers=AUTH_HEADERS,
        json={
            "name": "Updated playlist",
            "description": "New details",
            "items": [
                {"media_asset_id": str(second_media.id), "position": 2},
                {
                    "media_asset_id": str(first_media.id),
                    "position": 1,
                    "duration_seconds": 20,
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated playlist"
    assert body["description"] == "New details"
    assert body["version"] == playlist.version + 1
    assert [item["media_asset_id"] for item in body["items"]] == [
        str(first_media.id),
        str(second_media.id),
    ]
    assert body["items"][0]["duration_seconds"] == 20
    assert old_media.id not in {UUID(item["media_asset_id"]) for item in body["items"]}

    sync_state = await integration_session.get(ScreenSyncStateModel, screen.id)
    assert sync_state is not None
    assert sync_state.desired_revision == 1


async def test_update_playlist_rejects_missing_media_without_changing_playlist(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    existing_media = await create_media(integration_session, "Existing")
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Keep me", user_id=USER_ID)
    )
    await SqlAlchemyPlaylistItemRepository(integration_session).save(
        PlaylistItem(playlist_id=playlist.id, media_asset_id=existing_media.id, position=1)
    )
    await integration_session.commit()

    response = await client.put(
        f"/api/v1/playlists/{playlist.id}",
        headers=AUTH_HEADERS,
        json={
            "name": "Changed",
            "items": [{"media_asset_id": str(uuid4()), "position": 1}],
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"
    persisted = await SqlAlchemyPlaylistRepository(integration_session).get_by_id(
        playlist.id,
        user_id=USER_ID,
    )
    assert persisted is not None
    assert persisted.name == "Keep me"
    assert [item.media_asset_id for item in persisted.items] == [existing_media.id]


async def test_update_playlist_returns_not_found_for_unknown_playlist(
    client: httpx.AsyncClient,
) -> None:
    response = await client.put(
        f"/api/v1/playlists/{uuid4()}",
        headers=AUTH_HEADERS,
        json={"name": "Updated", "items": []},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PLAYLIST_NOT_FOUND"


async def test_update_playlist_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.put(
        f"/api/v1/playlists/{uuid4()}",
        json={"name": "Updated", "items": []},
    )

    assert response.status_code == 401
