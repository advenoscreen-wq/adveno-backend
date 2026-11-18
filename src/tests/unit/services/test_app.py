"""Tests for the application bootstrap."""

from fastapi.testclient import TestClient

from config.settings import Settings
from drivers.core.app import create_app


def test_health_endpoint_returns_ok(test_settings: Settings) -> None:
    """The health endpoint does not require business features."""
    app = create_app(test_settings)
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_reports_dependency_failure(test_settings: Settings) -> None:
    """Readiness returns service unavailable when a critical dependency fails."""
    app = create_app(test_settings, database_check=lambda: False)
    response = TestClient(app).get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
