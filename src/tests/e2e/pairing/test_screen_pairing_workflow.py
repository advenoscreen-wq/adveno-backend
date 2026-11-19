"""End-to-end tests for new-screen and reconnect pairing workflows."""

import hashlib
from datetime import timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import SqlAlchemyScreenRepository
from domain import Screen
from domain.entities.common import utc_now
from domain.value_object import PairingSessionStatus, PairingType, ScreenStatus
from drivers.database.models.entities import (
    ScreenCredentialModel,
    ScreenModel,
    ScreenPairingSessionModel,
    ScreenSyncStateModel,
)
from tests.e2e.helpers import create_paired_screen

pytestmark = [pytest.mark.integration, pytest.mark.e2e]

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}
PAIRING_SESSIONS_URL = "/api/v1/pairing/sessions"


async def test_new_screen_pairing_completes_tv_and_dashboard_workflow(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    created = await pairing_client.post(
        PAIRING_SESSIONS_URL,
        json={"pairing_type": PairingType.NEW_SCREEN.value},
    )
    assert created.status_code == 201
    created_body = created.json()
    session_id = str(created_body["session_id"])
    pairing_token = str(created_body["pairing_token"])
    tv_headers = {"X-Pairing-Token": pairing_token}
    dashboard_headers = {**AUTH_HEADERS, **tv_headers}

    assert set(created_body) == {"session_id", "pairing_token", "expires_at"}
    assert await integration_session.scalar(select(func.count()).select_from(ScreenModel)) == 0
    assert (
        await integration_session.scalar(
            select(func.count()).select_from(ScreenPairingSessionModel)
        )
        == 1
    )

    pending = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/{session_id}",
        headers=tv_headers,
    )
    assert pending.status_code == 200
    assert pending.json() == {"status": PairingSessionStatus.PENDING.value}

    early_screen = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/{session_id}/screen",
        headers=dashboard_headers,
        json={"name": "Should not exist"},
    )
    assert early_screen.status_code == 409
    assert early_screen.json()["error"]["code"] == "PAIRING_SESSION_NOT_PAIRED"

    verified_pending = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/verify",
        headers={**dashboard_headers},
    )
    assert verified_pending.status_code == 200
    assert verified_pending.json()["status"] == PairingSessionStatus.PENDING.value
    assert verified_pending.json()["screen_exists"] is False

    approval = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/approve",
        headers=dashboard_headers,
        json={},
    )
    assert approval.status_code == 200
    assert approval.json()["status"] == PairingSessionStatus.CONNECTING.value
    assert approval.json()["screen_id"] is None
    assert approval.json()["paired_at"] is None

    connecting = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/{session_id}",
        headers=tv_headers,
    )
    assert connecting.json() == {"status": PairingSessionStatus.CONNECTING.value}

    screen_response = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/{session_id}/screen",
        headers=dashboard_headers,
        json={"name": "Conference TV", "device_model": "Model Y", "app_version": "2.1"},
    )
    assert screen_response.status_code == 201
    screen_body = screen_response.json()
    screen_id = UUID(str(screen_body["screen_id"]))
    raw_credential = screen_body["credential"]

    paired = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/{session_id}",
        headers=tv_headers,
    )
    assert paired.json() == {"status": PairingSessionStatus.PAIRED.value}
    verified_paired = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/verify",
        headers=dashboard_headers,
    )
    assert verified_paired.status_code == 200
    assert verified_paired.json()["status"] == PairingSessionStatus.PAIRED.value
    assert verified_paired.json()["screen_exists"] is True
    assert verified_paired.json()["screen_id"] == str(screen_id)

    screen = await integration_session.get(ScreenModel, screen_id)
    sync_state = await integration_session.get(ScreenSyncStateModel, screen_id)
    session = await integration_session.get(ScreenPairingSessionModel, UUID(session_id))
    credential = await integration_session.scalar(
        select(ScreenCredentialModel).where(
            ScreenCredentialModel.screen_id == screen_id,
            ScreenCredentialModel.revoked_at.is_(None),
        )
    )
    assert screen is not None
    assert screen.user_id == USER_ID
    assert screen.name == "Conference TV"
    assert screen.device_model == "Model Y"
    assert screen.app_version == "2.1"
    assert screen.screen_code == screen_body["screen_code"]
    assert sync_state is not None
    assert (sync_state.desired_revision, sync_state.applied_revision) == (0, 0)
    assert session is not None
    assert session.status == PairingSessionStatus.PAIRED.value
    assert session.screen_id == screen_id
    assert session.paired_at is not None
    assert credential is not None
    assert credential.credential_hash == hashlib.sha256(raw_credential.encode()).hexdigest()
    assert raw_credential != credential.credential_hash

    initial_sync = await pairing_client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )
    assert initial_sync.status_code == 200
    assert initial_sync.json() == {"need_sync": False, "desired_revision": 0}

    replay = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/{session_id}/screen",
        headers=dashboard_headers,
        json={"name": "Duplicate TV"},
    )
    assert replay.status_code == 409
    assert replay.json()["error"]["code"] == "PAIRING_SCREEN_ALREADY_CREATED"


async def test_reconnect_pairing_preserves_screen_and_rotates_credential(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen_body = await create_paired_screen(
        pairing_client,
        name="Lobby display",
    )
    screen_id = UUID(screen_body["screen_id"])
    old_credential = str(screen_body["credential"])

    playlist_response = await pairing_client.post(
        "/api/v1/playlists",
        headers=AUTH_HEADERS,
        json={"name": "Lobby playlist", "description": "Must be preserved", "items": []},
    )
    assert playlist_response.status_code == 201
    playlist_id = playlist_response.json()["id"]
    assignment_response = await pairing_client.put(
        f"/api/v1/screens/{screen_id}/playlist",
        headers=AUTH_HEADERS,
        json={"playlist_id": playlist_id},
    )
    assert assignment_response.status_code == 200

    original_screen = await integration_session.get(ScreenModel, screen_id)
    original_credential = await integration_session.scalar(
        select(ScreenCredentialModel).where(
            ScreenCredentialModel.screen_id == screen_id,
            ScreenCredentialModel.revoked_at.is_(None),
        )
    )
    assert original_screen is not None
    original_code = original_screen.screen_code
    assert original_credential is not None
    original_credential_id = original_credential.id

    reconnect = await pairing_client.post(
        PAIRING_SESSIONS_URL,
        json={"pairing_type": PairingType.RECONNECT_EXISTING.value},
    )
    assert reconnect.status_code == 201
    reconnect_id = str(reconnect.json()["session_id"])
    reconnect_token = str(reconnect.json()["pairing_token"])
    reconnect_headers = {**AUTH_HEADERS, "X-Pairing-Token": reconnect_token}

    approved = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/approve",
        headers=reconnect_headers,
        json={"screen_id": str(screen_id)},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == PairingSessionStatus.CONNECTING.value
    assert approved.json()["screen_id"] == str(screen_id)

    persisted_old_credential = await integration_session.get(
        ScreenCredentialModel,
        original_credential_id,
    )
    assert persisted_old_credential is not None
    await integration_session.refresh(persisted_old_credential)
    assert persisted_old_credential.revoked_at is not None

    accidental_new_screen = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/{reconnect_id}/screen",
        headers=reconnect_headers,
        json={"name": "Must remain the same screen"},
    )
    assert accidental_new_screen.status_code == 422
    assert accidental_new_screen.json()["error"]["code"] == "NEW_SCREEN_PAIRING_REQUIRED"

    credential_response = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/{reconnect_id}/credential",
        headers={"X-Pairing-Token": reconnect_token},
    )
    assert credential_response.status_code == 200
    new_credential = str(credential_response.json()["credential"])
    assert credential_response.json()["screen_id"] == str(screen_id)

    status_response = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/{reconnect_id}",
        headers={"X-Pairing-Token": reconnect_token},
    )
    assert status_response.json() == {"status": PairingSessionStatus.PAIRED.value}

    final_screen = await integration_session.get(ScreenModel, screen_id)
    active_credential = await integration_session.scalar(
        select(ScreenCredentialModel).where(
            ScreenCredentialModel.screen_id == screen_id,
            ScreenCredentialModel.revoked_at.is_(None),
        )
    )
    assert final_screen is not None
    assert final_screen.screen_code == original_code
    assert final_screen.user_id == USER_ID
    assert active_credential is not None
    assert active_credential.credential_hash == hashlib.sha256(new_credential.encode()).hexdigest()
    assert new_credential != old_credential

    old_tv_request = await pairing_client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {old_credential}"},
    )
    assert old_tv_request.status_code == 401
    assert old_tv_request.json()["error"]["code"] == "SCREEN_DISCONNECTED"

    new_tv_request = await pairing_client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {new_credential}"},
    )
    assert new_tv_request.status_code == 200
    sync_result = new_tv_request.json()
    assert sync_result["need_sync"] is True
    assert sync_result["desired_revision"] > 0


async def test_pairing_edge_cases_reject_invalid_auth_tokens_and_expired_sessions(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    invalid_type = await pairing_client.post(
        PAIRING_SESSIONS_URL,
        json={"pairing_type": "UNKNOWN"},
    )
    assert invalid_type.status_code == 422

    created = await pairing_client.post(
        PAIRING_SESSIONS_URL,
        json={"pairing_type": PairingType.NEW_SCREEN.value},
    )
    assert created.status_code == 201
    session_id = str(created.json()["session_id"])
    pairing_token = str(created.json()["pairing_token"])

    missing_token = await pairing_client.get(f"{PAIRING_SESSIONS_URL}/{session_id}")
    assert missing_token.status_code == 422

    wrong_token = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/{session_id}",
        headers={"X-Pairing-Token": "not-the-token"},
    )
    assert wrong_token.status_code == 404
    assert wrong_token.json()["error"]["code"] == "PAIRING_SESSION_NOT_FOUND"

    unauthenticated_approval = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/approve",
        headers={"X-Pairing-Token": pairing_token},
        json={},
    )
    assert unauthenticated_approval.status_code == 401

    wrong_mode = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/approve",
        headers={**AUTH_HEADERS, "X-Pairing-Token": pairing_token},
        json={"screen_id": str(uuid4())},
    )
    assert wrong_mode.status_code == 422
    assert wrong_mode.json()["error"]["code"] == "SCREEN_ID_NOT_ALLOWED"

    session = await integration_session.get(ScreenPairingSessionModel, UUID(session_id))
    assert session is not None
    session.expires_at = utc_now() - timedelta(seconds=1)
    await integration_session.commit()

    expired_approval = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/approve",
        headers={**AUTH_HEADERS, "X-Pairing-Token": pairing_token},
        json={},
    )
    assert expired_approval.status_code == 410
    assert expired_approval.json()["error"]["code"] == "PAIRING_SESSION_EXPIRED"

    expired_status = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/{session_id}",
        headers={"X-Pairing-Token": pairing_token},
    )
    assert expired_status.status_code == 200
    assert expired_status.json() == {"status": PairingSessionStatus.EXPIRED.value}
    assert await integration_session.scalar(select(func.count()).select_from(ScreenModel)) == 0


async def test_reconnect_approval_rejects_missing_unknown_and_inactive_screens(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    inactive_screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(
            user_id=USER_ID,
            name="Inactive TV",
            status=ScreenStatus.INACTIVE,
        )
    )
    await integration_session.commit()

    created = await pairing_client.post(
        PAIRING_SESSIONS_URL,
        json={"pairing_type": PairingType.RECONNECT_EXISTING.value},
    )
    assert created.status_code == 201
    headers = {
        **AUTH_HEADERS,
        "X-Pairing-Token": str(created.json()["pairing_token"]),
    }

    missing_screen_id = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/approve",
        headers=headers,
        json={},
    )
    assert missing_screen_id.status_code == 422
    assert missing_screen_id.json()["error"]["code"] == "SCREEN_ID_REQUIRED"

    unknown_screen = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/approve",
        headers=headers,
        json={"screen_id": str(uuid4())},
    )
    assert unknown_screen.status_code == 404
    assert unknown_screen.json()["error"]["code"] == "SCREEN_NOT_FOUND"

    inactive_screen_response = await pairing_client.post(
        f"{PAIRING_SESSIONS_URL}/approve",
        headers=headers,
        json={"screen_id": str(inactive_screen.id)},
    )
    assert inactive_screen_response.status_code == 409
    assert inactive_screen_response.json()["error"]["code"] == "SCREEN_NOT_ELIGIBLE"

    still_pending = await pairing_client.get(
        f"{PAIRING_SESSIONS_URL}/{created.json()['session_id']}",
        headers={"X-Pairing-Token": headers["X-Pairing-Token"]},
    )
    assert still_pending.json() == {"status": PairingSessionStatus.PENDING.value}
