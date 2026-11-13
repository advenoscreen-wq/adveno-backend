"""Integration test for the health endpoint."""

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_health_endpoint_returns_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
