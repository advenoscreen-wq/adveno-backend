"""Integration test for the readiness endpoint."""

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_ready_endpoint_reports_ready(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
