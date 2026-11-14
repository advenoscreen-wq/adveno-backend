"""Integration test for the readiness endpoint."""

import httpx
import pytest
from fastapi import FastAPI

from drivers.routers.dependencies import get_database_ready

pytestmark = pytest.mark.integration


async def test_ready_endpoint_reports_ready(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_ready_endpoint_reports_unavailable_when_database_check_fails(
    api_app: FastAPI,
) -> None:
    api_app.dependency_overrides[get_database_ready] = lambda: False
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://testserver",
    ) as unavailable_client:
        response = await unavailable_client.get("/api/v1/ready")

    assert response.status_code == 503
