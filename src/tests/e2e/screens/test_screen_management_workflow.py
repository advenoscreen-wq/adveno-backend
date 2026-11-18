"""End-to-end screen management, disconnection, and deletion workflow."""

import httpx
import pytest

from tests.e2e.helpers import create_paired_screen

pytestmark = [pytest.mark.integration, pytest.mark.e2e]

AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_screen_management_rename_unassign_disconnect_and_delete(
    client: httpx.AsyncClient,
) -> None:
    created = await create_paired_screen(client, name="Old screen name")
    screen_id = str(created["screen_id"])
    credential = str(created["credential"])

    renamed = await client.patch(
        f"/api/v1/screens/{screen_id}",
        headers=AUTH_HEADERS,
        json={"name": "Reception display"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Reception display"

    listed = await client.get(
        "/api/v1/screens",
        headers=AUTH_HEADERS,
        params={"filter_by_name": "reception", "page": 1, "limit": 10},
    )
    assert listed.status_code == 200
    assert listed.json()["total_items"] == 1
    assert listed.json()["items"][0]["id"] == screen_id

    playlist = await client.post(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        json={"name": "Reception rotation", "items": []},
    )
    assert playlist.status_code == 201
    assignment = await client.put(
        f"/api/v1/screens/{screen_id}/playlist",
        headers=AUTH_HEADERS,
        json={"playlist_id": playlist.json()["id"]},
    )
    assert assignment.status_code == 200
    details = await client.get(f"/api/v1/screens/{screen_id}", headers=AUTH_HEADERS)
    assert details.json()["assigned_playlist"]["id"] == playlist.json()["id"]

    unassigned = await client.delete(
        f"/api/v1/screens/{screen_id}/playlist",
        headers=AUTH_HEADERS,
    )
    assert unassigned.status_code == 204
    tv_playlist = await client.get(
        "/api/v1/screens/assigned-playlist",
        headers={"Authorization": f"Bearer {credential}"},
    )
    assert tv_playlist.status_code == 200
    assert tv_playlist.json() is None

    disconnected = await client.post(
        f"/api/v1/screens/{screen_id}/disconnect",
        headers=AUTH_HEADERS,
    )
    assert disconnected.status_code == 204
    tv_request = await client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {credential}"},
    )
    assert tv_request.status_code == 401
    assert tv_request.json()["error"]["code"] == "SCREEN_DISCONNECTED"

    deleted = await client.delete(f"/api/v1/screens/{screen_id}", headers=AUTH_HEADERS)
    assert deleted.status_code == 204
    missing = await client.get(f"/api/v1/screens/{screen_id}", headers=AUTH_HEADERS)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "SCREEN_NOT_FOUND"
