"""Integration tests for screen pairing session APIs."""

import hashlib
from datetime import datetime, timedelta
from uuid import UUID

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.common import utc_now
from domain.value_object import PairingSessionStatus, PairingType
from drivers.database.models.entities import ScreenModel, ScreenPairingSessionModel

pytestmark = pytest.mark.integration


async def test_create_pairing_session_returns_token_and_persists_hash(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    missing_type_response = await pairing_client.post("/api/v1/pairing/sessions")
    assert missing_type_response.status_code == 422
    screen_id_response = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.NEW_SCREEN.value, "screen_id": str(UUID(int=1))},
    )
    assert screen_id_response.status_code == 422

    response = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.NEW_SCREEN.value},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"session_id", "pairing_token", "expires_at"}
    session_id = UUID(body["session_id"])
    pairing_token = body["pairing_token"]
    stored = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(ScreenPairingSessionModel.id == session_id)
    )

    assert stored is not None
    assert stored.token_hash == hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    assert stored.token_hash != pairing_token
    assert stored.pairing_type == PairingType.NEW_SCREEN.value
    assert stored.screen_id is None
    assert stored.status == PairingSessionStatus.PENDING.value
    assert stored.paired_at is None

    reconnect_response = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.RECONNECT_EXISTING.value},
    )
    assert reconnect_response.status_code == 201
    reconnect_session_id = UUID(reconnect_response.json()["session_id"])
    reconnect_session = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(
            ScreenPairingSessionModel.id == reconnect_session_id
        )
    )
    assert reconnect_session is not None
    assert reconnect_session.pairing_type == PairingType.RECONNECT_EXISTING.value
    assert reconnect_session.screen_id is None
    screen_count = await integration_session.scalar(
        select(func.count()).select_from(ScreenModel)
    )
    assert screen_count == 0

    verify_url = "/api/v1/pairing/sessions/verify"
    unauthenticated_response = await pairing_client.get(
        verify_url,
        headers={"X-Pairing-Token": pairing_token},
    )
    assert unauthenticated_response.status_code == 401

    verify_response = await pairing_client.get(
        verify_url,
        headers={
            "Authorization": "Bearer valid-access-token",
            "X-Pairing-Token": pairing_token,
        },
    )
    assert verify_response.status_code == 200
    verify_body = verify_response.json()
    assert verify_body["session_id"] == str(session_id)
    assert verify_body["status"] == PairingSessionStatus.PENDING.value
    assert verify_body["pairing_type"] == PairingType.NEW_SCREEN.value
    assert verify_body["screen_id"] is None
    assert verify_body["screen_exists"] is False
    assert datetime.fromisoformat(verify_body["expires_at"]) == stored.expires_at
    assert datetime.fromisoformat(verify_body["created_at"]) == stored.created_at

    invalid_access_response = await pairing_client.get(
        verify_url,
        headers={
            "Authorization": "Bearer invalid-access-token",
            "X-Pairing-Token": pairing_token,
        },
    )
    assert invalid_access_response.status_code == 401

    missing_session_response = await pairing_client.get(
        verify_url,
        headers={
            "Authorization": "Bearer valid-access-token",
            "X-Pairing-Token": "unknown-token",
        },
    )
    assert missing_session_response.status_code == 404
    assert missing_session_response.json()["error"]["code"] == "PAIRING_SESSION_NOT_FOUND"

    status_response = await pairing_client.get(
        f"/api/v1/pairing/sessions/{session_id}",
        headers={"X-Pairing-Token": pairing_token},
    )
    assert status_response.status_code == 200
    assert status_response.json() == {"status": PairingSessionStatus.PENDING.value}

    stored.expires_at = utc_now() - timedelta(seconds=1)
    await integration_session.flush()
    expired_response = await pairing_client.get(
        verify_url,
        headers={
            "Authorization": "Bearer valid-access-token",
            "X-Pairing-Token": pairing_token,
        },
    )
    assert expired_response.status_code == 200
    assert expired_response.json()["status"] == PairingSessionStatus.EXPIRED.value

    invalid_token_response = await pairing_client.get(
        f"/api/v1/pairing/sessions/{session_id}",
        headers={"X-Pairing-Token": "invalid-token"},
    )
    assert invalid_token_response.status_code == 404
    assert invalid_token_response.json()["error"]["code"] == "PAIRING_SESSION_NOT_FOUND"
