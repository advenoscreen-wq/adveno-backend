"""Integration tests for screen credential verification."""

import hashlib
from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import SqlAlchemyScreenRepository
from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from domain import Screen, ScreenCredential
from domain.value_object import ScreenStatus

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


async def test_verification_accepts_active_credential_and_records_heartbeat(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "verify-active-screen-token"
    screen_repository = SqlAlchemyScreenRepository(integration_session)
    credential_repository = SqlAlchemyScreenCredentialRepository(integration_session)
    screen = await screen_repository.save(Screen(user_id=USER_ID, name="Lobby TV"))
    credential = await credential_repository.save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
    )
    await integration_session.commit()

    response = await client.post(
        "/api/v1/screens/credential/verify",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )

    assert response.status_code == 200
    assert response.json() == {"valid": True}
    integration_session.expire_all()
    updated_screen = await screen_repository.get_by_id(screen.id)
    updated_credential = await credential_repository.get_by_id(credential.id)
    assert updated_screen is not None and updated_screen.last_seen_at is not None
    assert updated_credential is not None and updated_credential.last_used_at is not None


async def test_verification_rejects_unknown_credential(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/screens/credential/verify",
        headers={"Authorization": "Bearer unknown-screen-token"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCREEN_NOT_FOUND"


async def test_verification_requires_bearer_credential(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/screens/credential/verify")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_SCREEN_CREDENTIAL"


async def test_verification_rejects_revoked_or_inactive_screen(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    for index, screen_status in enumerate((ScreenStatus.ACTIVE, ScreenStatus.INACTIVE)):
        raw_credential = f"disconnected-screen-token-{index}"
        screen = await SqlAlchemyScreenRepository(integration_session).save(
            Screen(user_id=USER_ID, name=f"TV {index}", status=screen_status)
        )
        credential = ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
        if index == 0:
            credential.revoke()
        await SqlAlchemyScreenCredentialRepository(integration_session).save(credential)
        await integration_session.commit()

        response = await client.post(
            "/api/v1/screens/credential/verify",
            headers={"Authorization": f"Bearer {raw_credential}"},
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "SCREEN_DISCONNECTED"
