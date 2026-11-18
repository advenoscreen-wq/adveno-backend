"""End-to-end process and dependency readiness checks."""

import httpx
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]


async def test_health_and_readiness_report_live_services(client: httpx.AsyncClient) -> None:
    health = await client.get("/api/v1/health")
    readiness = await client.get("/api/v1/ready")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ready"}
