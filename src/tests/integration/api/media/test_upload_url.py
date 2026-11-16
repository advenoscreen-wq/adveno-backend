"""Integration tests for requesting media upload URLs."""

from unittest.mock import Mock

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_upload_url_returns_signed_url_and_user_scoped_storage_path(
    client: httpx.AsyncClient,
    storage_service: Mock,
) -> None:
    response = await client.post(
        "/api/v1/media/upload-url",
        headers={"Authorization": "Bearer valid-access-token"},
        json={"file_name": "welcome image.png"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["signed_url"] == "https://storage.example/signed-upload"
    assert body["storage_path"].startswith("users/00000000-0000-0000-0000-000000000099/")
    assert body["storage_path"].endswith("/welcome image.png")
    storage_service.create_signed_upload_url.assert_awaited_once()
    kwargs = storage_service.create_signed_upload_url.await_args.kwargs
    assert kwargs["bucket"] == "media"
    assert kwargs["access_token"] == "valid-access-token"
    assert kwargs["object_path"] == body["storage_path"]


@pytest.mark.parametrize("authorization", [None, "Bearer invalid-access-token"])
async def test_upload_url_requires_authenticated_user(
    client: httpx.AsyncClient,
    storage_service: Mock,
    authorization: str | None,
) -> None:
    headers = {"Authorization": authorization} if authorization else {}
    response = await client.post(
        "/api/v1/media/upload-url",
        headers=headers,
        json={"file_name": "welcome.png"},
    )

    assert response.status_code == 401
    storage_service.create_signed_upload_url.assert_not_awaited()


@pytest.mark.parametrize(
    "payload",
    [{}, {"file_name": "../outside.png"}, {"file_name": "folder/file.png"}],
)
async def test_upload_url_rejects_invalid_file_name(
    client: httpx.AsyncClient,
    storage_service: Mock,
    payload: dict[str, str],
) -> None:
    response = await client.post(
        "/api/v1/media/upload-url",
        headers={"Authorization": "Bearer valid-access-token"},
        json=payload,
    )

    assert response.status_code == 422
    storage_service.create_signed_upload_url.assert_not_awaited()
