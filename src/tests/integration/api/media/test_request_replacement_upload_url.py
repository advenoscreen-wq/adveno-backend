"""Integration tests for requesting an upload URL to replace owned media."""

from unittest.mock import Mock
from uuid import UUID

import httpx
import pytest

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
STORAGE_PATH = f"users/{USER_ID}/replacement-test/original.png"


async def test_replacement_upload_url_targets_existing_media_path(
    client: httpx.AsyncClient,
    storage_service: Mock,
) -> None:
    headers = {"Authorization": "Bearer valid-access-token"}
    created = await client.post(
        "/api/v1/media",
        headers=headers,
        json={
            "name": "Original image",
            "media_type": "IMAGE",
            "mime_type": "image/png",
            "storage_path": STORAGE_PATH,
            "file_size": 100,
        },
    )
    assert created.status_code == 201
    media_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/media/{media_id}/upload-url",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "signed_url": "https://storage.example/signed-upload",
        "storage_path": STORAGE_PATH,
    }
    storage_service.create_signed_upload_url.assert_awaited_once_with(
        bucket="media",
        object_path=STORAGE_PATH,
        access_token="valid-access-token",
        upsert=True,
    )


async def test_replacement_upload_url_returns_not_found_for_unknown_media(
    client: httpx.AsyncClient,
    storage_service: Mock,
) -> None:
    response = await client.post(
        "/api/v1/media/00000000-0000-0000-0000-000000000123/upload-url",
        headers={"Authorization": "Bearer valid-access-token"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"
    storage_service.create_signed_upload_url.assert_not_awaited()


async def test_replacement_upload_url_requires_authentication(
    client: httpx.AsyncClient,
    storage_service: Mock,
) -> None:
    response = await client.post(
        "/api/v1/media/00000000-0000-0000-0000-000000000123/upload-url",
    )

    assert response.status_code == 401
    storage_service.create_signed_upload_url.assert_not_awaited()
