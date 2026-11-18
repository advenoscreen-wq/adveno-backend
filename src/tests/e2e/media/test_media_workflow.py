"""End-to-end media upload registration, retrieval, and replacement workflow."""

from unittest.mock import Mock

import httpx
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]

AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_media_upload_registration_listing_and_replacement_workflow(
    client: httpx.AsyncClient,
    storage_service: Mock,
) -> None:
    upload = await client.post(
        "/api/v1/media/upload-url",
        headers=AUTH_HEADERS,
        json={"file_name": "lobby-banner.png"},
    )
    assert upload.status_code == 200
    upload_details = upload.json()
    assert upload_details["signed_url"] == "https://storage.example/signed-upload"

    created = await client.post(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        json={
            "name": "Lobby banner",
            "media_type": "IMAGE",
            "mime_type": "image/png",
            "storage_path": upload_details["storage_path"],
            "file_size": 4096,
            "width": 1920,
            "height": 1080,
        },
    )
    assert created.status_code == 201
    original = created.json()
    assert original["checksum"]
    assert original["media_url"].endswith(original["storage_path"])

    fetched = await client.get(f"/api/v1/media/{original['id']}", headers=AUTH_HEADERS)
    listed = await client.get(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        params={"filter_by_name": "lobby", "page": 1, "limit": 10},
    )
    assert fetched.status_code == 200
    assert fetched.json()["checksum"] == original["checksum"]
    assert listed.status_code == 200
    assert listed.json()["total_items"] == 1
    assert listed.json()["items"][0]["id"] == original["id"]

    replacement_upload = await client.post(
        f"/api/v1/media/{original['id']}/upload-url",
        headers=AUTH_HEADERS,
    )
    assert replacement_upload.status_code == 200
    replacement_path = replacement_upload.json()["storage_path"]

    replacement = await client.put(
        f"/api/v1/media/{original['id']}",
        headers=AUTH_HEADERS,
        json={
            "is_replaced": True,
            "name": "Lobby video",
            "media_type": "VIDEO",
            "mime_type": "video/mp4",
            "storage_path": replacement_path,
            "file_size": 8192,
            "duration_seconds": 40,
        },
    )
    assert replacement.status_code == 200
    updated = replacement.json()
    assert updated["name"] == "Lobby video"
    assert updated["media_type"] == "VIDEO"
    assert updated["duration_seconds"] == 40
    assert updated["storage_path"] == replacement_path
    assert updated["checksum"] != original["checksum"]
    assert updated["media_url"].endswith(replacement_path)
    assert updated["screen_sync"] == []
    assert storage_service.create_signed_upload_url.await_count == 2
