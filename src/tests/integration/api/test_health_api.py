"""Integration tests for the bootstrap health endpoints."""

import pytest
from fastapi.testclient import TestClient

from config.settings import Settings
from drivers.core.app import create_app


@pytest.mark.integration
def test_health_and_ready_endpoints_are_exposed() -> None:
    """The versioned HTTP boundary exposes operational endpoints."""
    app = create_app(
        Settings(environment="test", database_url="postgresql+asyncpg://unused"),
        database_check=lambda: True,
    )
    client = TestClient(app)

    assert client.get("/api/v1/health").json() == {"status": "ok"}
    assert client.get("/api/v1/ready").json() == {"status": "ready"}
