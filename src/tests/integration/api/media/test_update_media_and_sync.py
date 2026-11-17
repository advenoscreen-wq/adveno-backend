"""Integration tests for media updates and playlist screen synchronization."""

from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyPlaylistItemRepository,
    SqlAlchemyPlaylistRepository,
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
)
from domain import Playlist, PlaylistItem, Screen, ScreenPlaylistAssignment
from domain.value_object import MediaType
from drivers.database.models.screen_sync_state import ScreenSyncStateModel

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def create_media(client: httpx.AsyncClient) -> dict[str, object]:
    response = await client.post(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        json={
            "name": "Original banner",
            "media_type": "IMAGE",
            "mime_type": "image/png",
            "storage_path": f"users/{USER_ID}/{uuid4().hex}/original.png",
            "file_size": 1024,
            "width": 1280,
            "height": 720,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


async def assign_media_to_screens(
    session: AsyncSession,
    *,
    media_id: UUID,
    count: int,
) -> list[Screen]:
    screens = [
        await SqlAlchemyScreenRepository(session).save(
            Screen(user_id=USER_ID, name=f"Display {index}")
        )
        for index in range(count)
    ]
    playlist = await SqlAlchemyPlaylistRepository(session).save(
        Playlist(name="Lobby playlist", user_id=USER_ID)
    )
    await SqlAlchemyPlaylistItemRepository(session).save(
        PlaylistItem(playlist_id=playlist.id, media_asset_id=media_id, position=1)
    )
    assignment_repository = SqlAlchemyScreenPlaylistAssignmentRepository(session)
    for screen in screens:
        await assignment_repository.save(
            ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
        )
    await session.commit()
    return screens


async def test_update_without_replacement_changes_name_only(
    client: httpx.AsyncClient,
) -> None:
    original = await create_media(client)
    response = await client.put(
        f"/api/v1/media/{original['id']}",
        headers=AUTH_HEADERS,
        json={"is_replaced": False, "name": "Lobby banner"},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Lobby banner"
    assert updated["storage_path"] == original["storage_path"]
    assert updated["file_size"] == original["file_size"]
    assert updated["mime_type"] == original["mime_type"]
    assert updated["checksum"] == original["checksum"]
    assert updated["screen_sync"] == []


async def test_replacement_updates_file_fields_and_syncs_every_assigned_screen(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    original = await create_media(client)
    screens = await assign_media_to_screens(
        integration_session,
        media_id=UUID(str(original["id"])),
        count=2,
    )
    replacement_path = f"users/{USER_ID}/{uuid4().hex}/replacement.jpg"

    response = await client.put(
        f"/api/v1/media/{original['id']}",
        headers=AUTH_HEADERS,
        json={
            "is_replaced": True,
            "name": "Updated banner",
            "media_type": "IMAGE",
            "mime_type": "image/jpeg",
            "storage_path": replacement_path,
            "file_size": 4096,
            "width": 1920,
            "height": 1080,
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Updated banner"
    assert updated["storage_path"] == replacement_path
    assert updated["file_size"] == 4096
    assert updated["mime_type"] == "image/jpeg"
    assert updated["checksum"] != original["checksum"]
    assert {item["screen_id"] for item in updated["screen_sync"]} == {
        str(screen.id) for screen in screens
    }
    assert {item["desired_revision"] for item in updated["screen_sync"]} == {1}

    states = await integration_session.scalars(select(ScreenSyncStateModel))
    assert {state.screen_id: state.desired_revision for state in states} == {
        screen.id: 1 for screen in screens
    }


async def test_video_replacement_updates_playlist_item_durations_and_versions(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    original = await create_media(client)
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Video playlist", user_id=USER_ID)
    )
    await SqlAlchemyPlaylistItemRepository(integration_session).save(
        PlaylistItem(
            playlist_id=playlist.id,
            media_asset_id=UUID(str(original["id"])),
            position=1,
            duration_seconds=10,
        )
    )
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Video screen")
    )
    await SqlAlchemyScreenPlaylistAssignmentRepository(integration_session).save(
        ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
    )
    await integration_session.commit()

    response = await client.put(
        f"/api/v1/media/{original['id']}",
        headers=AUTH_HEADERS,
        json={
            "is_replaced": True,
            "name": "Updated video",
            "media_type": MediaType.VIDEO.value,
            "mime_type": "video/mp4",
            "storage_path": f"users/{USER_ID}/{uuid4().hex}/video.mp4",
            "file_size": 4096,
            "duration_seconds": 45,
        },
    )

    assert response.status_code == 200
    items = await SqlAlchemyPlaylistItemRepository(integration_session).list_by_media_asset_id(
        UUID(str(original["id"]))
    )
    assert len(items) == 1
    assert items[0].duration_seconds == 45
    updated_playlist = await SqlAlchemyPlaylistRepository(integration_session).get_by_id(
        playlist.id,
        user_id=USER_ID,
    )
    assert updated_playlist is not None
    assert updated_playlist.version == playlist.version + 1


async def test_image_replacement_preserves_playlist_item_duration(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    original = await create_media(client)
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Image playlist", user_id=USER_ID)
    )
    await SqlAlchemyPlaylistItemRepository(integration_session).save(
        PlaylistItem(
            playlist_id=playlist.id,
            media_asset_id=UUID(str(original["id"])),
            position=1,
            duration_seconds=20,
        )
    )
    await integration_session.commit()

    response = await client.put(
        f"/api/v1/media/{original['id']}",
        headers=AUTH_HEADERS,
        json={
            "is_replaced": True,
            "name": "Updated image",
            "media_type": MediaType.IMAGE.value,
            "mime_type": "image/jpeg",
            "storage_path": f"users/{USER_ID}/{uuid4().hex}/image.jpg",
            "file_size": 2048,
        },
    )

    assert response.status_code == 200
    items = await SqlAlchemyPlaylistItemRepository(integration_session).list_by_media_asset_id(
        UUID(str(original["id"]))
    )
    assert len(items) == 1
    assert items[0].duration_seconds == 20


async def test_update_rejects_replacement_without_file_metadata(
    client: httpx.AsyncClient,
) -> None:
    original = await create_media(client)
    response = await client.put(
        f"/api/v1/media/{original['id']}",
        headers=AUTH_HEADERS,
        json={"is_replaced": True},
    )

    assert response.status_code == 422


async def test_update_rejects_video_replacement_without_duration(
    client: httpx.AsyncClient,
) -> None:
    original = await create_media(client)
    response = await client.put(
        f"/api/v1/media/{original['id']}",
        headers=AUTH_HEADERS,
        json={
            "is_replaced": True,
            "name": "Updated video",
            "media_type": MediaType.VIDEO.value,
            "mime_type": "video/mp4",
            "storage_path": f"users/{USER_ID}/{uuid4().hex}/video.mp4",
            "file_size": 4096,
        },
    )

    assert response.status_code == 422


async def test_update_rejects_file_fields_when_not_replaced(
    client: httpx.AsyncClient,
) -> None:
    original = await create_media(client)
    response = await client.put(
        f"/api/v1/media/{original['id']}",
        headers=AUTH_HEADERS,
        json={
            "is_replaced": False,
            "name": "Renamed banner",
            "file_size": 512,
        },
    )

    assert response.status_code == 422


async def test_update_returns_not_found_for_an_unknown_media(
    client: httpx.AsyncClient,
) -> None:
    response = await client.put(
        f"/api/v1/media/{uuid4()}",
        headers=AUTH_HEADERS,
        json={"is_replaced": False, "name": "Missing"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"


async def test_update_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.put(
        f"/api/v1/media/{uuid4()}",
        json={"is_replaced": False, "name": "Unauthenticated"},
    )

    assert response.status_code == 401
