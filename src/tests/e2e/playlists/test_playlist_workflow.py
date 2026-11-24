"""End-to-end playlist creation, playback delivery, update, and deletion."""

from uuid import UUID, uuid4

import httpx
import pytest

from tests.e2e.helpers import create_paired_screen

pytestmark = [pytest.mark.integration, pytest.mark.e2e]

AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}
USER_ID = UUID("00000000-0000-0000-0000-000000000099")


async def test_playlist_workflow_reaches_tv_and_deletion_removes_assignment(
    client: httpx.AsyncClient,
) -> None:
    media_response = await client.post(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        json={
            "name": "Welcome image",
            "media_type": "IMAGE",
            "mime_type": "image/png",
            "storage_path": f"users/{USER_ID}/{uuid4().hex}/welcome.png",
            "file_size": 1024,
            "width": 1280,
            "height": 720,
        },
    )
    assert media_response.status_code == 201
    media = media_response.json()

    empty_playlist = await client.post(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        json={"name": "Welcome loop", "description": "Lobby welcome"},
    )
    assert empty_playlist.status_code == 201
    playlist_id = empty_playlist.json()["id"]
    assert empty_playlist.json()["items"] == []

    playlist_read = await client.get(
        f"/api/v1/playlists/{playlist_id}",
        headers=AUTH_HEADERS,
    )
    assert playlist_read.status_code == 200
    assert playlist_read.json()["items"] == []

    playlist_update = await client.put(
        f"/api/v1/playlists/{playlist_id}",
        headers=AUTH_HEADERS,
        json={
            "name": "Welcome loop updated",
            "description": "Daily lobby welcome",
            "items": [{"media_asset_id": media["id"], "position": 1, "duration_seconds": 12}],
        },
    )
    assert playlist_update.status_code == 200
    updated_playlist = playlist_update.json()
    assert updated_playlist["version"] > empty_playlist.json()["version"]
    assert updated_playlist["items"][0]["media_asset_id"] == media["id"]

    listed = await client.get(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        params={"filter_by_title": "lobby", "page": 1, "limit": 10},
    )
    assert listed.status_code == 200
    assert listed.json()["total_items"] == 1
    assert listed.json()["items"][0]["id"] == playlist_id

    screen = await create_paired_screen(client, name="Lobby playback screen")
    screen_id = str(screen["screen_id"])
    device_credential = str(screen["credential"])
    assignment = await client.put(
        f"/api/v1/screens/{screen_id}/playlist",
        headers=AUTH_HEADERS,
        json={"playlist_id": playlist_id},
    )
    assert assignment.status_code == 200

    screen_details = await client.get(
        f"/api/v1/screens/{screen_id}",
        headers=AUTH_HEADERS,
    )
    assert screen_details.status_code == 200
    assert screen_details.json()["assigned_playlist"]["id"] == playlist_id

    tv_playlist = await client.get(
        "/api/v1/screens/assigned-playlist",
        headers={"Authorization": f"Bearer {device_credential}"},
    )
    assert tv_playlist.status_code == 200
    tv_item = tv_playlist.json()["items"][0]
    assert tv_item["duration_seconds"] == 12
    assert tv_item["media"]["checksum"] == media["checksum"]
    assert tv_item["media"]["media_url"] == media["media_url"]

    sync_check = await client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {device_credential}"},
    )
    assert sync_check.status_code == 200
    sync_result = sync_check.json()
    assert sync_result["need_sync"] is True
    assert sync_result["desired_revision"] > 0

    deleted = await client.delete(
        f"/api/v1/playlists/{playlist_id}",
        headers=AUTH_HEADERS,
    )
    assert deleted.status_code == 204
    tv_playlist_after_delete = await client.get(
        "/api/v1/screens/assigned-playlist",
        headers={"Authorization": f"Bearer {device_credential}"},
    )
    assert tv_playlist_after_delete.status_code == 200
    assert tv_playlist_after_delete.json() == {"playlist": None, "items": []}
    missing_playlist = await client.get(
        f"/api/v1/playlists/{playlist_id}",
        headers=AUTH_HEADERS,
    )
    assert missing_playlist.status_code == 404
