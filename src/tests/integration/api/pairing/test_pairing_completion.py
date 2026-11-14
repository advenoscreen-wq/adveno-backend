"""Integration tests for checking pairing completion."""

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.common import utc_now
from domain.value_object import PairingType
from drivers.database.models.entities import ScreenCredentialModel, ScreenPairingSessionModel

pytestmark = pytest.mark.integration
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_completion_is_false_while_pending(pairing_client: httpx.AsyncClient) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    response = await pairing_client.get(
        "/api/v1/pairing/sessions/completion",
        headers={"X-Pairing-Token": created.json()["pairing_token"]},
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False


async def test_completion_is_false_until_screen_has_active_credential(
    pairing_client: httpx.AsyncClient, integration_session: AsyncSession
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    token = created.json()["pairing_token"]
    headers = {**AUTH_HEADERS, "X-Pairing-Token": token}
    await pairing_client.post("/api/v1/pairing/sessions/approve", headers=headers, json={})
    response = await pairing_client.get(
        "/api/v1/pairing/sessions/completion", headers={"X-Pairing-Token": token}
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False
    session = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(
            ScreenPairingSessionModel.id == created.json()["session_id"]
        )
    )
    assert session is not None and session.screen_id is None


async def test_completion_is_false_when_screen_credential_is_revoked(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    token = created.json()["pairing_token"]
    headers = {**AUTH_HEADERS, "X-Pairing-Token": token}
    await pairing_client.post("/api/v1/pairing/sessions/approve", headers=headers, json={})
    screen = await pairing_client.post(
        f"/api/v1/pairing/sessions/{created.json()['session_id']}/screen",
        headers=headers,
        json={"name": "Lobby TV"},
    )
    credential = await integration_session.scalar(
        select(ScreenCredentialModel).where(
            ScreenCredentialModel.screen_id == screen.json()["screen_id"]
        )
    )
    assert credential is not None
    credential.revoked_at = utc_now()
    await integration_session.commit()

    response = await pairing_client.get(
        "/api/v1/pairing/sessions/completion", headers={"X-Pairing-Token": token}
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False


async def test_completion_is_true_after_screen_and_credential_exist(
    pairing_client: httpx.AsyncClient,
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    token = created.json()["pairing_token"]
    headers = {**AUTH_HEADERS, "X-Pairing-Token": token}
    await pairing_client.post("/api/v1/pairing/sessions/approve", headers=headers, json={})
    await pairing_client.post(
        f"/api/v1/pairing/sessions/{created.json()['session_id']}/screen",
        headers=headers,
        json={"name": "Lobby TV"},
    )
    response = await pairing_client.get(
        "/api/v1/pairing/sessions/completion", headers={"X-Pairing-Token": token}
    )

    assert response.status_code == 200
    assert response.json()["completed"] is True


async def test_completion_returns_not_found_for_unknown_token(
    pairing_client: httpx.AsyncClient,
) -> None:
    response = await pairing_client.get(
        "/api/v1/pairing/sessions/completion", headers={"X-Pairing-Token": "unknown"}
    )

    assert response.status_code == 404


async def test_completion_requires_token_header(pairing_client: httpx.AsyncClient) -> None:
    response = await pairing_client.get("/api/v1/pairing/sessions/completion")

    assert response.status_code == 422
