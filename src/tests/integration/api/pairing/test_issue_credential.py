"""Integration tests for issuing and rotating paired screen credentials."""

import hashlib
from uuid import UUID

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.value_object import PairingType
from drivers.database.models.entities import (
    ScreenCredentialModel,
    ScreenPairingSessionModel,
    ScreenSyncStateModel,
)

pytestmark = pytest.mark.integration
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_credential_endpoint_issues_one_active_credential_for_registered_screen(
    pairing_client: httpx.AsyncClient, integration_session: AsyncSession
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions", json={"pairing_type": PairingType.NEW_SCREEN.value}
    )
    token = created.json()["pairing_token"]
    headers = {**AUTH_HEADERS, "X-Pairing-Token": token}
    await pairing_client.post("/api/v1/pairing/sessions/approve", headers=headers, json={})
    screen_response = await pairing_client.post(
        f"/api/v1/pairing/sessions/{created.json()['session_id']}/screen",
        headers=headers,
        json={"name": "Lobby"},
    )
    screen_id = UUID(screen_response.json()["screen_id"])
    original_credential_id = await integration_session.scalar(
        select(ScreenCredentialModel.id).where(
            ScreenCredentialModel.screen_id == screen_id,
            ScreenCredentialModel.revoked_at.is_(None),
        )
    )
    assert original_credential_id is not None

    response = await pairing_client.post(
        f"/api/v1/pairing/sessions/{created.json()['session_id']}/credential",
        headers={"X-Pairing-Token": token},
    )

    assert response.status_code == 200
    credential = response.json()["credential"]
    assert response.json()["screen_id"] == str(screen_id)
    session = await integration_session.get(
        ScreenPairingSessionModel, UUID(created.json()["session_id"])
    )
    assert session is not None
    assert session.status == "PAIRED"
    assert session.paired_at is not None
    stored = await integration_session.scalar(
        select(ScreenCredentialModel).where(
            ScreenCredentialModel.screen_id == screen_id,
            ScreenCredentialModel.credential_hash
            == hashlib.sha256(credential.encode()).hexdigest(),
        )
    )
    assert stored is not None
    original_credential = await integration_session.get(
        ScreenCredentialModel, original_credential_id
    )
    assert original_credential is not None
    assert original_credential.revoked_at is not None
    assert (
        await integration_session.scalar(
            select(func.count()).where(ScreenCredentialModel.screen_id == screen_id)
        )
        == 2
    )
    assert (
        await integration_session.scalar(
            select(func.count())
            .select_from(ScreenCredentialModel)
            .where(
                ScreenCredentialModel.screen_id == screen_id,
                ScreenCredentialModel.revoked_at.is_(None),
            )
        )
        == 1
    )
    integration_session.expire_all()
    sync_state = await integration_session.get(ScreenSyncStateModel, screen_id)
    assert sync_state is not None
    assert sync_state.desired_revision == 2
    assert sync_state.applied_revision == 0


async def test_credential_endpoint_rejects_unknown_session(
    pairing_client: httpx.AsyncClient,
) -> None:
    response = await pairing_client.post(
        f"/api/v1/pairing/sessions/{UUID(int=1)}/credential", headers={"X-Pairing-Token": "unknown"}
    )

    assert response.status_code == 404
