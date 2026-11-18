"""End-to-end OAuth login, refresh, and provider denial workflows."""

from unittest.mock import Mock

import httpx
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]


async def test_google_login_sets_session_cookie_then_refreshes_tokens(
    client: httpx.AsyncClient,
    oauth_provider: Mock,
) -> None:
    authorization = await client.get("/api/v1/auth/google/request")

    assert authorization.status_code == 307
    assert "code_challenge_method=s256" in authorization.headers["location"]
    state_cookie = client.cookies.get("adveno_oauth_state")
    assert state_cookie

    callback = await client.get(
        "/api/v1/auth/google/callback",
        params={"code": "e2e-authorization-code"},
    )
    assert callback.status_code == 303
    assert callback.headers["location"] == "http://localhost:3000/login"
    assert callback.cookies.get("adveno_session") == "refresh-token"
    oauth_provider.exchange_code.assert_awaited_once()

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": callback.cookies["adveno_session"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json() == {
        "access_token": "new-access-token",
        "refresh_token": "rotated-refresh-token",
        "token_type": "bearer",
        "expires_in": 3600,
    }
    oauth_provider.refresh_access_token.assert_awaited_once_with("refresh-token")


async def test_google_login_reports_signup_disabled_provider_error(
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
