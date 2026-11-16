"""Unit tests for the Supabase Storage adapter using mocked HTTP responses."""

import httpx
import pytest

from adapters.services.storage.supabase_storage_service import SupabaseStorageService
from application.exceptions.storage import StorageServiceError


@pytest.mark.asyncio
async def test_create_signed_upload_url_returns_supabase_upload_url() -> None:
    captured_request: httpx.Request | None = None

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(
            200,
            json={"url": "/object/upload/sign/media/folder/image%20one.png?token=upload-token"},
        )

    service = SupabaseStorageService(
        supabase_url="https://example.supabase.co",
        supabase_anon_key="anon-key",
        transport=httpx.MockTransport(respond),
    )

    signed_url = await service.create_signed_upload_url(
        bucket="media",
        object_path="folder/image one.png",
        access_token="user-access-token",
    )

    assert signed_url == (
        "https://example.supabase.co/storage/v1"
        "/object/upload/sign/media/folder/image%20one.png?token=upload-token"
    )
    assert captured_request is not None
    assert captured_request.method == "POST"
    assert captured_request.url.raw_path == (
        b"/storage/v1/object/upload/sign/media/folder/image%20one.png"
    )
    assert captured_request.headers["apikey"] == "anon-key"
    assert captured_request.headers["authorization"] == "Bearer user-access-token"


@pytest.mark.asyncio
async def test_create_signed_upload_url_builds_url_from_storage_token() -> None:
    service = SupabaseStorageService(
        supabase_url="https://example.supabase.co/",
        supabase_anon_key="anon-key",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"token": "token value"})),
    )

    signed_url = await service.create_signed_upload_url(
        bucket="media",
        object_path="image.png",
        access_token="user-access-token",
    )

    assert signed_url == (
        "https://example.supabase.co/storage/v1/object/upload/sign/media/image.png"
        "?token=token+value"
    )


@pytest.mark.asyncio
async def test_create_signed_upload_url_maps_provider_failure() -> None:
    service = SupabaseStorageService(
        supabase_url="https://example.supabase.co",
        supabase_anon_key="anon-key",
        transport=httpx.MockTransport(lambda _: httpx.Response(403)),
    )

    with pytest.raises(StorageServiceError):
        await service.create_signed_upload_url(
            bucket="media",
            object_path="image.png",
            access_token="user-access-token",
        )


@pytest.mark.parametrize("object_path", ["", "/image.png", "../image.png", "folder//image.png"])
@pytest.mark.asyncio
async def test_create_signed_upload_url_rejects_invalid_object_path(
    object_path: str,
) -> None:
    service = SupabaseStorageService(
        supabase_url="https://example.supabase.co",
        supabase_anon_key="anon-key",
    )

    with pytest.raises(ValueError, match="object_path"):
        await service.create_signed_upload_url(
            bucket="media",
            object_path=object_path,
            access_token="user-access-token",
        )
