"""Integration tests for the auth refresh endpoint."""

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_refresh_returns_access_and_rotated_refresh_tokens(
    client: httpx.AsyncClient,
    refresh_token_calls: list[str],
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
    assert refresh_token_calls == ["current-refresh-token"]
