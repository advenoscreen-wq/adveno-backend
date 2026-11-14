"""Integration tests for authenticated pairing session verification."""

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


async def test_verify_returns_session_details_for_valid_user_and_token(
    pairing_client: httpx.AsyncClient,
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    token = created.json()["pairing_token"]
    response = await pairing_client.get(
        "/api/v1/pairing/sessions/verify",
        headers={"Authorization": "Bearer valid-access-token", "X-Pairing-Token": token},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == created.json()["session_id"]
    assert body["status"] == PairingSessionStatus.PENDING.value
    assert body["pairing_type"] == PairingType.NEW_SCREEN.value
    assert body["screen_id"] is None
    assert body["screen_exists"] is False
    assert body["expires_at"] and body["created_at"]


@pytest.mark.parametrize("authorization", [None, "Bearer invalid-access-token"])
async def test_verify_requires_valid_user(
    pairing_client: httpx.AsyncClient, authorization: str | None
) -> None:
    headers = {"X-Pairing-Token": "any-token"}
    if authorization:
        headers["Authorization"] = authorization
    response = await pairing_client.get("/api/v1/pairing/sessions/verify", headers=headers)

    assert response.status_code == 401


async def test_verify_returns_not_found_for_unknown_token(
    pairing_client: httpx.AsyncClient,
) -> None:
    response = await pairing_client.get(
        "/api/v1/pairing/sessions/verify",
        headers={"Authorization": "Bearer valid-access-token", "X-Pairing-Token": "unknown-token"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PAIRING_SESSION_NOT_FOUND"


async def test_verify_reports_expired_session(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.NEW_SCREEN.value},
    )
    session = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(
            ScreenPairingSessionModel.id == UUID(created.json()["session_id"])
        )
    )
    assert session is not None
    session.expires_at = utc_now() - timedelta(seconds=1)
    await integration_session.commit()

    response = await pairing_client.get(
        "/api/v1/pairing/sessions/verify",
        headers={
            "Authorization": "Bearer valid-access-token",
            "X-Pairing-Token": created.json()["pairing_token"],
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == PairingSessionStatus.EXPIRED.value
