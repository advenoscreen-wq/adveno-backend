"""Integration tests for the TV pairing status endpoint."""

from datetime import timedelta
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.common import utc_now
from domain.value_object import PairingSessionStatus, PairingType
from drivers.database.models.entities import ScreenPairingSessionModel

pytestmark = pytest.mark.integration


async def test_status_returns_pending_for_matching_session_and_token(
    pairing_client: httpx.AsyncClient,
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    response = await pairing_client.get(
        f"/api/v1/pairing/sessions/{created.json()['session_id']}",
        headers={"X-Pairing-Token": created.json()["pairing_token"]},
    )

    assert response.status_code == 200
    assert response.json() == {"status": PairingSessionStatus.PENDING.value}


async def test_status_rejects_wrong_token(pairing_client: httpx.AsyncClient) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    response = await pairing_client.get(
        f"/api/v1/pairing/sessions/{created.json()['session_id']}",
        headers={"X-Pairing-Token": "wrong-token"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PAIRING_SESSION_NOT_FOUND"


async def test_status_returns_not_found_for_unknown_session(
    pairing_client: httpx.AsyncClient,
) -> None:
    response = await pairing_client.get(
        f"/api/v1/pairing/sessions/{UUID(int=1)}", headers={"X-Pairing-Token": "any-token"}
    )

    assert response.status_code == 404


async def test_status_requires_pairing_token_header(pairing_client: httpx.AsyncClient) -> None:
    response = await pairing_client.get(f"/api/v1/pairing/sessions/{UUID(int=1)}")

    assert response.status_code == 422


async def test_status_reports_expired_session(
    pairing_client: httpx.AsyncClient, integration_session: AsyncSession
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    session_id = UUID(created.json()["session_id"])
    session = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(ScreenPairingSessionModel.id == session_id)
    )
    assert session is not None
    session.expires_at = utc_now() - timedelta(seconds=1)
    await integration_session.commit()

    response = await pairing_client.get(
        f"/api/v1/pairing/sessions/{session_id}",
        headers={"X-Pairing-Token": created.json()["pairing_token"]},
    )

    assert response.status_code == 200
    assert response.json() == {"status": PairingSessionStatus.EXPIRED.value}
