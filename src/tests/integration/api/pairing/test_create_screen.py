"""Integration tests for creating a screen after pairing."""

import hashlib
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.value_object import PairingSessionStatus, PairingType
from drivers.database.models.entities import (
    ScreenCredentialModel,
    ScreenModel,
    ScreenPairingSessionModel,
    ScreenSyncStateModel,
)

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_create_screen_requires_connecting_session(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.NEW_SCREEN.value},
    )
    session_id = UUID(created.json()["session_id"])
    pairing_token = created.json()["pairing_token"]
    headers = {**AUTH_HEADERS, "X-Pairing-Token": pairing_token}
    body = {"name": "Lobby TV", "device_model": "Model X", "app_version": "1.2.3"}

    pending = await pairing_client.post(
        f"/api/v1/pairing/sessions/{session_id}/screen",
        headers=headers,
        json=body,
    )
    assert pending.status_code == 409
    assert pending.json()["error"]["code"] == "PAIRING_SESSION_NOT_PAIRED"
    assert await integration_session.scalar(select(ScreenModel.id).limit(1)) is None
    approved = await pairing_client.post(
        "/api/v1/pairing/sessions/approve",
        headers=headers,
        json={},
    )
    assert approved.status_code == 200
    response = await pairing_client.post(
        f"/api/v1/pairing/sessions/{session_id}/screen",
        headers=headers,
        json=body,
    )
    assert response.status_code == 201
    result = response.json()
    screen_id = UUID(result["screen_id"])

    screen = await integration_session.scalar(
        select(ScreenModel).where(ScreenModel.id == screen_id)
    )
    session = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(ScreenPairingSessionModel.id == session_id)
    )
    assert screen is not None
    assert screen.user_id == USER_ID
    assert screen.name == body["name"]
    assert screen.device_model == body["device_model"]
    assert screen.app_version == body["app_version"]
    assert screen.screen_code == result["screen_code"]
    sync_state = await integration_session.get(ScreenSyncStateModel, screen_id)
    assert sync_state is not None
    assert sync_state.desired_revision == 0
    assert sync_state.applied_revision == 0
    assert sync_state.sync_status == "PENDING"
    credential = await integration_session.scalar(
        select(ScreenCredentialModel).where(ScreenCredentialModel.screen_id == screen_id)
    )
    assert credential is not None
    assert (
        credential.credential_hash
        == hashlib.sha256(result["credential"].encode("utf-8")).hexdigest()
    )
    assert result["credential"] != credential.credential_hash
    assert session is not None
    assert session.status == PairingSessionStatus.PAIRED.value
    assert session.screen_id == screen_id


async def test_create_screen_requires_authorization(
    pairing_client: httpx.AsyncClient,
) -> None:
    response = await pairing_client.post(
        f"/api/v1/pairing/sessions/{UUID(int=1)}/screen",
        headers={"X-Pairing-Token": "token"},
        json={"name": "TV"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("body", [{}, {"name": "TV", "unexpected": True}])
async def test_create_screen_rejects_invalid_body(
    pairing_client: httpx.AsyncClient, body: dict[str, str]
) -> None:
    response = await pairing_client.post(
        f"/api/v1/pairing/sessions/{UUID(int=1)}/screen",
        headers={**AUTH_HEADERS, "X-Pairing-Token": "token"},
        json=body,
    )

    assert response.status_code == 422


async def test_create_screen_requires_pairing_token(
    pairing_client: httpx.AsyncClient,
) -> None:
    response = await pairing_client.post(
        f"/api/v1/pairing/sessions/{UUID(int=1)}/screen",
        headers=AUTH_HEADERS,
        json={"name": "TV"},
    )

    assert response.status_code == 422
