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
)

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_create_screen_requires_paired_session_and_assigns_screen_id(
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
    incomplete = await pairing_client.get(
        "/api/v1/pairing/sessions/completion",
        headers=headers,
    )
    assert incomplete.status_code == 200
    assert incomplete.json()["completed"] is False

    approved = await pairing_client.post(
        "/api/v1/pairing/sessions/approve",
        headers=headers,
        json={},
    )
    assert approved.status_code == 200
    approved_but_unregistered = await pairing_client.get(
        "/api/v1/pairing/sessions/completion",
        headers=headers,
    )
    assert approved_but_unregistered.json()["completed"] is False

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
    credential = await integration_session.scalar(
        select(ScreenCredentialModel).where(ScreenCredentialModel.screen_id == screen_id)
    )
    assert credential is not None
    assert credential.credential_hash == hashlib.sha256(
        result["credential"].encode("utf-8")
    ).hexdigest()
    assert result["credential"] != credential.credential_hash
    assert session is not None
    assert session.status == PairingSessionStatus.PAIRED.value
    assert session.screen_id == screen_id

    complete = await pairing_client.get(
        "/api/v1/pairing/sessions/completion",
        headers=headers,
    )
    assert complete.status_code == 200
    assert complete.json()["completed"] is True

    old_credential_id = credential.id
    issued = await pairing_client.post(
        f"/api/v1/pairing/sessions/{session_id}/credential",
        headers=headers,
    )
    assert issued.status_code == 200
    replacement_credential = await integration_session.scalar(
        select(ScreenCredentialModel)
        .where(ScreenCredentialModel.screen_id == screen_id)
        .where(ScreenCredentialModel.revoked_at.is_(None))
    )
    old_credential = await integration_session.get(ScreenCredentialModel, old_credential_id)
    assert old_credential is not None
    assert old_credential.revoked_at is not None
    assert replacement_credential is not None
    assert replacement_credential.credential_hash == hashlib.sha256(
        issued.json()["credential"].encode("utf-8")
    ).hexdigest()
