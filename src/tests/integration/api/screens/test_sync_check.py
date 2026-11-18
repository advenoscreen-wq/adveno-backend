"""Integration tests for a TV screen's synchronization check."""

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
from domain.value_object import ScreenStatus

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


async def test_sync_check_returns_need_sync_and_records_heartbeat(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "tv-device-secret"
    screen_repository = SqlAlchemyScreenRepository(integration_session)
    credential_repository = SqlAlchemyScreenCredentialRepository(integration_session)
    screen = await screen_repository.save(Screen(user_id=USER_ID, name="Lobby TV"))
    credential = await credential_repository.save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
    )
    await SqlAlchemyScreenSyncStateRepository(integration_session).save(
        ScreenSyncState(screen_id=screen.id, desired_revision=3, applied_revision=2)
    )
    await integration_session.commit()

    response = await client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )

    assert response.status_code == 200
    assert response.json() == {"need_sync": True}
    updated_screen = await screen_repository.get_by_id(screen.id)
    updated_credential = await credential_repository.get_by_id(credential.id)
    assert updated_screen is not None and updated_screen.last_seen_at is not None
    assert updated_credential is not None and updated_credential.last_used_at is not None


async def test_sync_check_returns_false_when_revisions_match(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "already-synced-device"
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Synced TV")
    )
    await SqlAlchemyScreenCredentialRepository(integration_session).save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
    )
    await SqlAlchemyScreenSyncStateRepository(integration_session).save(
        ScreenSyncState(screen_id=screen.id, desired_revision=2, applied_revision=2)
    )
    await integration_session.commit()

    response = await client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )

    assert response.status_code == 200
    assert response.json() == {"need_sync": False}


async def test_sync_check_rejects_invalid_or_missing_device_credential(
    client: httpx.AsyncClient,
) -> None:
    for headers in ({}, {"Authorization": "Bearer invalid-device-secret"}):
        response = await client.post("/api/v1/screens/sync-check", headers=headers)
        assert response.status_code == (401 if not headers else 404)
        assert response.json()["error"]["code"] == (
            "INVALID_SCREEN_CREDENTIAL" if not headers else "SCREEN_NOT_FOUND"
        )


@pytest.mark.parametrize(
    ("screen_status", "revoked", "expected_code"),
    [
        (ScreenStatus.ACTIVE, True, "SCREEN_DISCONNECTED"),
        (ScreenStatus.INACTIVE, False, "SCREEN_DISCONNECTED"),
    ],
)
async def test_sync_check_requires_screen_to_be_connected(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
    screen_status: ScreenStatus,
    revoked: bool,
    expected_code: str,
) -> None:
    raw_credential = f"device-{screen_status}-{revoked}"
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Disconnected TV", status=screen_status)
    )
    credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
    )
    if revoked:
        credential.revoke()
    await SqlAlchemyScreenCredentialRepository(integration_session).save(credential)
    await integration_session.commit()

    response = await client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == expected_code
