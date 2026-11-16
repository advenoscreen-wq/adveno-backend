"""Integration tests for registering uploaded media metadata."""

from uuid import UUID

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drivers.database.models.media_asset import MediaAssetModel

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


def media_payload(*, storage_path: str | None = None) -> dict[str, object]:
    return {
        "name": "Lobby banner",
        "media_type": "IMAGE",
        "mime_type": "image/png",
        "storage_path": storage_path
        or f"users/{USER_ID}/69017861559a4426a41c97d011c32bc5/testfile.png",
        "file_size": 2048,
        "width": 1920,
        "height": 1080,
    }


async def test_create_media_persists_metadata_for_authenticated_user(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    response = await client.post(
        "/api/v1/media",
        headers={"Authorization": "Bearer valid-access-token"},
        json=media_payload(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Lobby banner"
    assert body["media_type"] == "IMAGE"
    assert body["mime_type"] == "image/png"
    assert body["storage_path"] == media_payload()["storage_path"]
    assert body["media_url"] == (
        f"https://project.supabase.co/storage/v1/object/public/media/{body['storage_path']}"
    )
    assert body["file_size"] == 2048
    assert body["checksum"]
    assert body["width"] == 1920
    assert body["height"] == 1080
    assert body["status"] == "ACTIVE"

    model = await integration_session.scalar(
        select(MediaAssetModel).where(MediaAssetModel.id == UUID(body["id"]))
    )
    assert model is not None
    assert model.user_id == USER_ID


async def test_create_media_generates_a_unique_checksum_for_each_asset(
    client: httpx.AsyncClient,
) -> None:
    first = await client.post(
        "/api/v1/media",
        headers={"Authorization": "Bearer valid-access-token"},
        json=media_payload(storage_path=f"users/{USER_ID}/checksum-test-one/file.png"),
    )
    second = await client.post(
        "/api/v1/media",
        headers={"Authorization": "Bearer valid-access-token"},
        json=media_payload(storage_path=f"users/{USER_ID}/checksum-test-two/file.png"),
    )

    assert first.status_code == second.status_code == 201
    assert first.json()["checksum"] != second.json()["checksum"]


async def test_create_media_rejects_storage_path_owned_by_another_user(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/media",
        headers={"Authorization": "Bearer valid-access-token"},
        json=media_payload(storage_path="users/00000000-0000-0000-0000-000000000001/object.png"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_MEDIA_CREATE_REQUEST"


async def test_create_media_rejects_missing_authentication(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/api/v1/media", json=media_payload())

    assert response.status_code == 401


async def test_create_media_rejects_invalid_metadata(
    client: httpx.AsyncClient,
) -> None:
    payload = media_payload()
    payload["file_size"] = -1
    response = await client.post(
        "/api/v1/media",
        headers={"Authorization": "Bearer valid-access-token"},
        json=payload,
    )

    assert response.status_code == 422


async def test_create_media_rejects_storage_path_already_registered(
    client: httpx.AsyncClient,
) -> None:
    headers = {"Authorization": "Bearer valid-access-token"}
    payload = media_payload()
    first = await client.post("/api/v1/media", headers=headers, json=payload)
    second = await client.post("/api/v1/media", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "MEDIA_ALREADY_REGISTERED"
