"""Integration tests for the Google OAuth callback endpoint."""

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_google_callback_sets_refresh_cookie_and_redirects(
    client: httpx.AsyncClient,
) -> None:
    await client.get("/api/v1/auth/google/request")

    response = await client.get(
        "/api/v1/auth/google/callback",
        params={"code": "authorization-code"},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "http://localhost:3000/login"
    assert response.cookies.get("adveno_session") == "refresh-token"
    assert "httponly" in response.headers["set-cookie"].lower()


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
