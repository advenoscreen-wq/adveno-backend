"""Integration tests for the Google OAuth request endpoint."""

import json
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from adapters.services.redis_cache_service import RedisCacheService

pytestmark = pytest.mark.integration


async def test_google_request_redirects_with_pkce_and_state_cookie(
    client: httpx.AsyncClient,
    oauth_provider: Mock,
    redis_service: RedisCacheService,
) -> None:
    response = await client.get("/api/v1/auth/google/request")

    authorization_params = parse_qs(urlparse(response.headers["location"]).query)
    assert response.status_code == 307
    assert authorization_params["code_challenge_method"] == ["s256"]
    state = client.cookies.get("adveno_oauth_state")
    assert state
    assert "httponly" in response.headers["set-cookie"].lower()
    oauth_provider.get_authorization_url.assert_awaited_once()
    cached_attempt = await redis_service.get(f"oauth:state:{state}")
    assert cached_attempt is not None
    assert json.loads(cached_attempt)["redirect_uri"] == (
        "http://localhost:8000/api/v1/auth/google/callback"
    )
