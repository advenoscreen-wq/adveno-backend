"""Integration tests for paginated media listing."""

from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def create_media(client: httpx.AsyncClient, name: str) -> dict[str, object]:
    response = await client.post(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        json={
            "name": name,
            "media_type": "IMAGE",
            "mime_type": "image/png",
            "storage_path": f"users/{USER_ID}/{uuid4().hex}/{name}.png",
            "file_size": 512,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


async def test_list_media_returns_pagination_metadata_and_media_urls(
    client: httpx.AsyncClient,
) -> None:
    created = [await create_media(client, f"Asset {index}") for index in range(3)]

    first_page = await client.get(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        params={"page": 1, "limit": 2},
    )
    second_page = await client.get(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        params={"page": 2, "limit": 2},
    )

    assert first_page.status_code == second_page.status_code == 200
    first_body = first_page.json()
    second_body = second_page.json()
    assert first_body["total_items"] == 3
    assert first_body["total_pages"] == 2
    assert first_body["has_next"] is True
    assert first_body["has_prev"] is False
    assert second_body["has_next"] is False
    assert second_body["has_prev"] is True
    assert all(
        item["media_url"].startswith("https://project.supabase.co/") for item in first_body["items"]
    )
    returned_ids = {item["id"] for item in first_body["items"] + second_body["items"]}
    assert returned_ids == {item["id"] for item in created}


async def test_list_media_filters_by_name_case_insensitively(
    client: httpx.AsyncClient,
) -> None:
    await create_media(client, "Lobby Banner")
    await create_media(client, "Lobby Poster")
    await create_media(client, "Kitchen Menu")

    response = await client.get(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        params={"filter_by_name": "lObBy"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 2
    assert {item["name"] for item in body["items"]} == {
        "Lobby Banner",
        "Lobby Poster",
    }


async def test_list_media_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/media")

    assert response.status_code == 401


@pytest.mark.parametrize("params", [{"page": 0}, {"limit": 0}, {"limit": 101}])
async def test_list_media_rejects_invalid_pagination_parameters(
    client: httpx.AsyncClient,
    params: dict[str, int],
) -> None:
    response = await client.get(
        "/api/v1/media",
        headers=AUTH_HEADERS,
        params=params,
    )

    assert response.status_code == 422
