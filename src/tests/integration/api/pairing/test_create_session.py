"""Integration tests for creating pairing sessions."""

import hashlib
from datetime import datetime
from uuid import UUID

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.value_object import PairingSessionStatus, PairingType
from drivers.database.models.entities import ScreenModel, ScreenPairingSessionModel

pytestmark = pytest.mark.integration


async def test_create_session_persists_only_token_hash_and_no_screen(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    response = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"session_id", "pairing_token", "expires_at"}
    session_id = UUID(body["session_id"])
    token = body["pairing_token"]
    session = await integration_session.get(ScreenPairingSessionModel, session_id)
    assert session is not None
    assert session.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert session.token_hash != token
    assert session.status == PairingSessionStatus.PENDING.value
    assert session.pairing_type == PairingType.NEW_SCREEN.value
    assert session.screen_id is None
    assert session.paired_at is None
    expires_at = datetime.fromisoformat(body["expires_at"])
    assert (expires_at - session.created_at).total_seconds() == pytest.approx(600, abs=1)
    assert await integration_session.scalar(select(func.count()).select_from(ScreenModel)) == 0


async def test_create_session_accepts_reconnect_type_without_screen_id(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    response = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.RECONNECT_EXISTING.value},
    )

    assert response.status_code == 201
    session = await integration_session.get(
        ScreenPairingSessionModel, UUID(response.json()["session_id"])
    )
    assert session is not None
    assert session.pairing_type == PairingType.RECONNECT_EXISTING.value
    assert session.screen_id is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"pairing_type": "INVALID"},
        {"pairing_type": "NEW_SCREEN", "screen_id": str(UUID(int=1))},
    ],
)
async def test_create_session_rejects_invalid_request(
    pairing_client: httpx.AsyncClient, payload: dict[str, str]
) -> None:
    response = await pairing_client.post("/api/v1/pairing/sessions", json=payload)

    assert response.status_code == 422
