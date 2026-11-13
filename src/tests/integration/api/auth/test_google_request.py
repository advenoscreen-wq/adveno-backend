"""Integration tests for the Google OAuth request endpoint."""

from urllib.parse import parse_qs, urlparse

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_google_request_redirects_with_pkce_and_state_cookie(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/auth/google/request")

    authorization_params = parse_qs(urlparse(response.headers["location"]).query)
    assert response.status_code == 307
    assert authorization_params["code_challenge_method"] == ["s256"]
    assert client.cookies.get("adveno_oauth_state")
    assert "httponly" in response.headers["set-cookie"].lower()
