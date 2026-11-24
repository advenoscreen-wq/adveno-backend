"""Integration tests for the screen assigned playlist endpoint."""

import hashlib
from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
)
from adapters.repositories.media_asset_repository import SqlAlchemyMediaAssetRepository
from adapters.repositories.playlist_item_repository import SqlAlchemyPlaylistItemRepository
from adapters.repositories.playlist_repository import SqlAlchemyPlaylistRepository
from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from domain import (
    MediaAsset,
    Playlist,
    PlaylistItem,
    Screen,
    ScreenCredential,
    ScreenPlaylistAssignment,
)
from domain.value_object import MediaType, ScreenStatus

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


async def test_assigned_playlist_returns_media_metadata_and_public_url(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "screen-playlist-secret"
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Lobby TV")
    )
    await SqlAlchemyScreenCredentialRepository(integration_session).save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
    )
    media = await SqlAlchemyMediaAssetRepository(integration_session).save(
        MediaAsset(
            name="Lobby video",
            media_type=MediaType.VIDEO,
            mime_type="video/mp4",
            storage_path=f"adveno/users/{USER_ID}/video.mp4",
            file_size=1024,
            checksum="checksum-v1",
            user_id=USER_ID,
            duration_seconds=45,
            width=1920,
            height=1080,
        )
    )
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Lobby loop", user_id=USER_ID, description="Lobby rotation")
    )
    await SqlAlchemyPlaylistItemRepository(integration_session).save(
        PlaylistItem(
            playlist_id=playlist.id,
            media_asset_id=media.id,
            position=1,
            duration_seconds=30,
        )
    )
    await SqlAlchemyScreenPlaylistAssignmentRepository(integration_session).save(
        ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
    )
    await integration_session.commit()

    response = await client.get(
        "/api/v1/screens/assigned-playlist",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["playlist"]["id"] == str(playlist.id)
    assert body["playlist"]["version"] == playlist.version
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["position"] == 1
    assert item["duration_seconds"] == 30
    assert item["media"]["id"] == str(media.id)
    assert item["media"]["checksum"] == media.checksum
    assert item["media"]["duration_seconds"] == 45
    assert item["media"]["media_url"].endswith(media.storage_path)


async def test_assigned_playlist_returns_null_when_screen_has_no_assignment(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "screen-without-playlist-secret"
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Unassigned TV")
    )
    await SqlAlchemyScreenCredentialRepository(integration_session).save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
    )
    await integration_session.commit()

    response = await client.get(
        "/api/v1/screens/assigned-playlist",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )

    assert response.status_code == 200
    assert response.json() == {"playlist": None, "items": []}


async def test_assigned_playlist_rejects_invalid_screen_credential(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/screens/assigned-playlist",
        headers={"Authorization": "Bearer invalid-screen-secret"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCREEN_NOT_FOUND"


async def test_assigned_playlist_requires_active_screen(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "inactive-screen-credential"
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Inactive TV", status=ScreenStatus.INACTIVE)
    )
    await SqlAlchemyScreenCredentialRepository(integration_session).save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
    )
    await integration_session.commit()

    response = await client.get(
        "/api/v1/screens/assigned-playlist",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SCREEN_DISCONNECTED"
