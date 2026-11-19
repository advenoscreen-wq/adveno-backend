"""Integration tests for screen synchronization acknowledgments."""

import hashlib
from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import SqlAlchemyScreenRepository
from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from adapters.repositories.screen_sync_state_repository import (
    SqlAlchemyScreenSyncStateRepository,
)
from domain import Screen, ScreenCredential, ScreenSyncState
from domain.value_object import SyncStatus

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


async def _create_screen_with_sync_state(
    session: AsyncSession,
    *,
    credential: str,
    desired_revision: int,
    applied_revision: int,
) -> tuple[Screen, SqlAlchemyScreenSyncStateRepository]:
    screen = await SqlAlchemyScreenRepository(session).save(Screen(user_id=USER_ID, name="Sync TV"))
    await SqlAlchemyScreenCredentialRepository(session).save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(credential.encode()).hexdigest(),
        )
    )
    state_repository = SqlAlchemyScreenSyncStateRepository(session)
    await state_repository.save(
        ScreenSyncState(
            screen_id=screen.id,
            desired_revision=desired_revision,
            applied_revision=applied_revision,
        )
    )
    await session.commit()
    return screen, state_repository


async def test_sync_acknowledgment_persists_revision_and_clears_sync_requirement(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "sync-ack-tv-secret"
    screen, state_repository = await _create_screen_with_sync_state(
        integration_session,
        credential=raw_credential,
        desired_revision=3,
        applied_revision=2,
    )

    response = await client.post(
        "/api/v1/screens/sync-acknowledgments",
        headers={"Authorization": f"Bearer {raw_credential}"},
        json={"applied_revision": 3},
    )

    assert response.status_code == 202
    assert response.content == b""
    integration_session.expire_all()
    state = await state_repository.get_by_screen_id(screen.id)
    assert state is not None
    assert state.applied_revision == 3
    assert state.sync_status is SyncStatus.SYNCED
    assert state.last_successful_sync_at is not None

    check = await client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )
    assert check.json() == {"need_sync": False, "desired_revision": 3}


async def test_sync_acknowledgment_rejects_revision_newer_than_desired(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "future-sync-ack-secret"
    screen, state_repository = await _create_screen_with_sync_state(
        integration_session,
        credential=raw_credential,
        desired_revision=2,
        applied_revision=1,
    )

    response = await client.post(
        "/api/v1/screens/sync-acknowledgments",
        headers={"Authorization": f"Bearer {raw_credential}"},
        json={"applied_revision": 3},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SYNC_REVISION_CONFLICT"
    integration_session.expire_all()
    state = await state_repository.get_by_screen_id(screen.id)
    assert state is not None and state.applied_revision == 1


async def test_stale_sync_acknowledgment_does_not_move_applied_revision_backwards(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "stale-sync-ack-secret"
    screen, state_repository = await _create_screen_with_sync_state(
        integration_session,
        credential=raw_credential,
        desired_revision=4,
        applied_revision=3,
    )

    response = await client.post(
        "/api/v1/screens/sync-acknowledgments",
        headers={"Authorization": f"Bearer {raw_credential}"},
        json={"applied_revision": 2},
    )

    assert response.status_code == 202
    integration_session.expire_all()
    state = await state_repository.get_by_screen_id(screen.id)
    assert state is not None and state.applied_revision == 3


async def test_sync_acknowledgment_validates_body_and_device_auth(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "invalid-body-sync-ack-secret"
    await _create_screen_with_sync_state(
        integration_session,
        credential=raw_credential,
        desired_revision=0,
        applied_revision=0,
    )
    invalid_body = await client.post(
        "/api/v1/screens/sync-acknowledgments",
        headers={"Authorization": f"Bearer {raw_credential}"},
        json={"applied_revision": -1},
    )
    assert invalid_body.status_code == 422

    missing_auth = await client.post(
        "/api/v1/screens/sync-acknowledgments",
        json={"applied_revision": 0},
    )
    assert missing_auth.status_code == 401
    assert missing_auth.json()["error"]["code"] == "INVALID_SCREEN_CREDENTIAL"
