"""Integration tests for the Google OAuth callback endpoint."""

from unittest.mock import Mock

import httpx
import pytest

from adapters.services.redis_cache_service import RedisCacheService

pytestmark = pytest.mark.integration


async def test_google_callback_sets_refresh_cookie_and_redirects(
    client: httpx.AsyncClient,
    oauth_provider: Mock,
    redis_service: RedisCacheService,
) -> None:
    await client.get("/api/v1/auth/google/request")
    state = client.cookies.get("adveno_oauth_state")

    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"code": "authorization-code"},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "http://localhost:3000/login"
    assert response.cookies.get("adveno_session") == "refresh-token"
    assert "httponly" in response.headers["set-cookie"].lower()
    oauth_provider.exchange_code.assert_awaited_once()
    assert state and await redis_service.get(f"oauth:state:{state}") is None


async def test_google_callback_serves_fragment_bridge_when_query_is_empty(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/auth/google/callback")

    assert response.status_code == 200
    assert "window.location.hash" in response.text
    assert '"error_description"' in response.text


async def test_google_callback_maps_signup_disabled_error(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/auth/google/callback",
        params={
            "error": "access_denied",
            "error_code": "signup_disabled",
            "error_description": "Signups not allowed for this instance",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SIGNUP_DISABLED"


async def test_google_callback_requires_state_cookie_when_code_is_present(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/auth/google/callback", params={"code": "authorization-code"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_OAUTH_STATE"


async def test_google_callback_rejects_state_not_stored_in_redis(
    client: httpx.AsyncClient,
) -> None:
    await client.get("/api/v1/auth/google/request")
    client.cookies.set(
        "adveno_oauth_state",
        "tampered-state",
        path="/api/v1/auth/google/callback",
    )

    response = await client.get(
        "/api/v1/auth/google/callback", params={"code": "authorization-code"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_OAUTH_STATE"


async def test_google_callback_maps_provider_access_denial(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"error": "access_denied", "error_description": "User cancelled"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "OAUTH_ACCESS_DENIED"
