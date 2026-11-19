"""Integration tests for screen-device logout."""

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

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


async def test_logout_revokes_credential_and_keeps_screen(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "tv-logout-secret"
    screen_repository = SqlAlchemyScreenRepository(integration_session)
    credential_repository = SqlAlchemyScreenCredentialRepository(integration_session)
    screen = await screen_repository.save(Screen(user_id=USER_ID, name="Lobby TV"))
    device_credential = await credential_repository.save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
    )
    await integration_session.commit()

    response = await client.post(
        "/api/v1/screens/logout",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )

    assert response.status_code == 204
    assert response.content == b""
    integration_session.expire_all()
    assert await screen_repository.get_by_id(screen.id) is not None
    revoked = await credential_repository.get_by_id(device_credential.id)
    assert revoked is not None and revoked.revoked_at is not None

    follow_up = await client.post(
        "/api/v1/screens/sync-check",
        headers={"Authorization": f"Bearer {raw_credential}"},
    )
    assert follow_up.status_code == 401
    assert follow_up.json()["error"]["code"] == "SCREEN_DISCONNECTED"


async def test_logout_requires_a_screen_credential(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/screens/logout")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_SCREEN_CREDENTIAL"
