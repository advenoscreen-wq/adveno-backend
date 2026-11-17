"""Integration tests for the auth refresh endpoint."""

from unittest.mock import Mock

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_refresh_returns_access_and_rotated_refresh_tokens(
    client: httpx.AsyncClient,
    oauth_provider: Mock,
) -> None:
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "current-refresh-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "refresh_token": "rotated-refresh-token",
        "token_type": "bearer",
        "expires_in": 3600,
    }
    oauth_provider.refresh_access_token.assert_awaited_once_with("current-refresh-token")


async def test_refresh_rejects_missing_refresh_token(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/auth/refresh", json={})

    assert response.status_code == 422


async def test_refresh_rejects_empty_refresh_token(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": ""})

    assert response.status_code == 422


async def test_refresh_fails_when_provider_does_not_rotate_refresh_token(
    client: httpx.AsyncClient,
    oauth_provider: Mock,
) -> None:
    from application.dtos.oauth import OAuthTokenResult

    oauth_provider.refresh_access_token.return_value = OAuthTokenResult(
        "new-access-token", None, "bearer", 3600
    )
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "current-refresh-token"}
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "OAUTH_PROVIDER_ERROR"
