"""Integration tests for pairing approval."""

from datetime import timedelta
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from adapters.repositories.user_repository import SqlAlchemyUserRepository
from domain import Screen, ScreenCredential, User
from domain.entities.common import utc_now
from domain.value_object import PairingSessionStatus, PairingType
from drivers.database.models.entities import (
    ScreenCredentialModel,
    ScreenModel,
    ScreenPairingSessionModel,
)

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_new_screen_approval_only_pairs_the_session(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.NEW_SCREEN.value},
    )
    assert created.status_code == 201
    session_id = UUID(created.json()["session_id"])
    pairing_token = created.json()["pairing_token"]

    response = await pairing_client.post(
        "/api/v1/pairing/sessions/approve",
        headers={**AUTH_HEADERS, "X-Pairing-Token": pairing_token},
        json={},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == str(session_id)
    assert body["pairing_type"] == PairingType.NEW_SCREEN.value
    assert body["status"] == PairingSessionStatus.PAIRED.value
    assert body["screen_id"] is None
    assert body["paired_at"] is not None

    session = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(ScreenPairingSessionModel.id == session_id)
    )
    assert session is not None
    assert session.status == PairingSessionStatus.PAIRED.value
    assert session.screen_id is None
    assert session.paired_at is not None
    assert await integration_session.scalar(select(ScreenModel.id).limit(1)) is None

    repeated = await pairing_client.post(
        "/api/v1/pairing/sessions/approve",
        headers={**AUTH_HEADERS, "X-Pairing-Token": pairing_token},
        json={},
    )
    assert repeated.status_code == 409


async def test_reconnect_approval_requires_owned_screen_and_preserves_it(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen_repository = SqlAlchemyScreenRepository(integration_session)
    credential_repository = SqlAlchemyScreenCredentialRepository(integration_session)
    screen = await screen_repository.save(Screen(user_id=USER_ID, name="Lobby"))
    original_credential = await credential_repository.save(
        ScreenCredential(screen_id=screen.id, credential_hash="existing-credential-hash")
    )
    original_code = screen.screen_code

    other_user_id = UUID("00000000-0000-0000-0000-000000000100")
    await SqlAlchemyUserRepository(integration_session).save(User(id=other_user_id))
    other_screen = await screen_repository.save(
        Screen(user_id=other_user_id, name="Private screen")
    )

    created = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.RECONNECT_EXISTING.value},
    )
    assert created.status_code == 201
    session_id = UUID(created.json()["session_id"])
    pairing_token = created.json()["pairing_token"]

    forbidden_screen = await pairing_client.post(
        "/api/v1/pairing/sessions/approve",
        headers={**AUTH_HEADERS, "X-Pairing-Token": pairing_token},
        json={"screen_id": str(other_screen.id)},
    )
    assert forbidden_screen.status_code == 404

    approved = await pairing_client.post(
        "/api/v1/pairing/sessions/approve",
        headers={**AUTH_HEADERS, "X-Pairing-Token": pairing_token},
        json={"screen_id": str(screen.id)},
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["status"] == PairingSessionStatus.PAIRED.value
    assert body["screen_id"] == str(screen.id)
    assert body["paired_at"] is not None

    persisted_session = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(ScreenPairingSessionModel.id == session_id)
    )
    persisted_screen = await integration_session.scalar(
        select(ScreenModel).where(ScreenModel.id == screen.id)
    )
    assert persisted_session is not None
    assert persisted_session.status == PairingSessionStatus.PAIRED.value
    assert persisted_session.screen_id == screen.id
    assert persisted_session.paired_at is not None
    assert persisted_screen is not None
    assert persisted_screen.user_id == USER_ID
    assert persisted_screen.screen_code == original_code
    assert persisted_screen.name == "Lobby"
    persisted_old_credential = await integration_session.get(
        ScreenCredentialModel,
        original_credential.id,
    )
    assert persisted_old_credential is not None
    assert persisted_old_credential.revoked_at is not None
    assert (
        await integration_session.scalar(
            select(ScreenCredentialModel.id).where(
                ScreenCredentialModel.screen_id == screen.id,
                ScreenCredentialModel.revoked_at.is_(None),
            )
        )
        is None
    )

    issued = await pairing_client.post(
        f"/api/v1/pairing/sessions/{session_id}/credential",
        headers={"X-Pairing-Token": pairing_token},
    )
    assert issued.status_code == 200
    active_credential = await integration_session.scalar(
        select(ScreenCredentialModel).where(
            ScreenCredentialModel.screen_id == screen.id,
            ScreenCredentialModel.revoked_at.is_(None),
        )
    )
    assert active_credential is not None


async def test_approval_rejects_expired_session(
    pairing_client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    created = await pairing_client.post(
        "/api/v1/pairing/sessions",
        json={"pairing_type": PairingType.NEW_SCREEN.value},
    )
    session_id = UUID(created.json()["session_id"])
    pairing_token = created.json()["pairing_token"]
    session = await integration_session.scalar(
        select(ScreenPairingSessionModel).where(ScreenPairingSessionModel.id == session_id)
    )
    assert session is not None
    session.expires_at = utc_now() - timedelta(seconds=1)
    await integration_session.flush()

    response = await pairing_client.post(
        "/api/v1/pairing/sessions/approve",
        headers={**AUTH_HEADERS, "X-Pairing-Token": pairing_token},
        json={},
    )

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "PAIRING_SESSION_EXPIRED"
