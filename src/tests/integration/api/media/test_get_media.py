"""Integration tests for retrieving an owned media asset."""

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_get_media_returns_media_asset_with_readable_url(
    client: httpx.AsyncClient,
) -> None:
    created = await client.post(
        "/api/v1/media",
        headers={"Authorization": "Bearer valid-access-token"},
        json={
            "name": "Lobby image",
            "media_type": "IMAGE",
            "mime_type": "image/png",
            "storage_path": "users/00000000-0000-0000-0000-000000000099/get-test/image.png",
            "file_size": 1024,
        },
    )
    media_id = created.json()["id"]

    response = await client.get(
        f"/api/v1/media/{media_id}",
        headers={"Authorization": "Bearer valid-access-token"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == media_id
    assert response.json()["media_url"] == (
        "https://project.supabase.co/storage/v1/object/public/media/"
        "users/00000000-0000-0000-0000-000000000099/get-test/image.png"
    )


async def test_get_media_returns_not_found_for_unknown_asset(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/media/00000000-0000-0000-0000-000000000123",
        headers={"Authorization": "Bearer valid-access-token"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"


async def test_get_media_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/media/00000000-0000-0000-0000-000000000123")

    assert response.status_code == 401
