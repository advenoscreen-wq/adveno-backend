"""Integration tests for PIN-protected screen settings access."""

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.screen_admin_session_repository import (
    SqlAlchemyScreenAdminSessionRepository,
)
from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from adapters.services.pin_hasher import ScryptPinHasher
from domain import Screen, ScreenAdminSession, ScreenCredential
from drivers.database.models.screen_admin_session import ScreenAdminSessionModel
from drivers.database.models.screen_credential import ScreenCredentialModel

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


async def test_dashboard_creates_short_lived_pin_for_owned_screen(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Protected Lobby TV")
    )
    await integration_session.commit()

    response = await client.post(
        f"/api/v1/screens/{screen.id}/admin-session",
        headers={"Authorization": "Bearer valid-access-token"},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"session_id", "pin", "expires_at"}
    assert len(body["pin"]) == 6 and body["pin"].isdigit()
    stored_session = await integration_session.get(
        ScreenAdminSessionModel, UUID(body["session_id"])
    )
    assert stored_session is not None
    assert stored_session.code_hash != body["pin"]
    assert stored_session.token_hash is None


async def test_tv_verifies_pin_receives_temporary_token_and_revokes_it(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    raw_credential = "screen-admin-session-credential"
    pin = "000042"
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Protected Lobby TV")
    )
    await SqlAlchemyScreenCredentialRepository(integration_session).save(
        ScreenCredential(
            screen_id=screen.id,
            credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
        )
    )
    now = datetime.now(UTC)
    pin_hash = await ScryptPinHasher().hash_pin(pin)
    pin_session = await SqlAlchemyScreenAdminSessionRepository(integration_session).save(
        ScreenAdminSession(
            screen_id=screen.id,
            code_hash=pin_hash,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(minutes=5),
        )
    )
    await integration_session.commit()

    verified = await client.post(
        "/api/v1/screens/admin-session/verify",
        headers={"Authorization": f"Bearer {raw_credential}"},
        json={"pin": pin},
    )

    assert verified.status_code == 200
    raw_session_token = verified.json()["session_token"]
    integration_session.expire_all()
    stored_session = await integration_session.get(ScreenAdminSessionModel, pin_session.id)
    assert stored_session is not None
    assert stored_session.code_hash != pin
    assert stored_session.token_hash == hashlib.sha256(raw_session_token.encode()).hexdigest()
    assert stored_session.token_hash != raw_session_token

    revoked = await client.post(
        "/api/v1/screens/admin-session/revoke",
        headers={
            "Authorization": f"Bearer {raw_credential}",
            "X-Admin-Session": raw_session_token,
        },
    )

    assert revoked.status_code == 204
    integration_session.expire_all()
    stored_session = await integration_session.get(ScreenAdminSessionModel, pin_session.id)
    assert stored_session is not None and stored_session.revoked_at is not None

    repeated = await client.post(
        "/api/v1/screens/admin-session/revoke",
        headers={
            "Authorization": f"Bearer {raw_credential}",
            "X-Admin-Session": raw_session_token,
        },
    )
    assert repeated.status_code == 401
    assert repeated.json()["error"]["code"] == "EXPIRED_SESSION"


async def test_logout_rejects_admin_session_created_for_another_screen(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen_credential = "screen-one-credential"
    other_session_token = "screen-two-admin-session-token"
    screen_repository = SqlAlchemyScreenRepository(integration_session)
    credential_repository = SqlAlchemyScreenCredentialRepository(integration_session)
    admin_session_repository = SqlAlchemyScreenAdminSessionRepository(integration_session)
    screen_one = await screen_repository.save(Screen(user_id=USER_ID, name="Screen One"))
    screen_two = await screen_repository.save(Screen(user_id=USER_ID, name="Screen Two"))
    credential = await credential_repository.save(
        ScreenCredential(
            screen_id=screen_one.id,
            credential_hash=hashlib.sha256(screen_credential.encode()).hexdigest(),
        )
    )
    now = datetime.now(UTC)
    await admin_session_repository.save(
        ScreenAdminSession(
            screen_id=screen_two.id,
            code_hash="stored-pin-hash",
            token_hash=hashlib.sha256(other_session_token.encode()).hexdigest(),
            created_at=now - timedelta(minutes=1),
            last_activity_at=now,
            expires_at=now + timedelta(minutes=14),
        )
    )
    await integration_session.commit()

    response = await client.post(
        "/api/v1/screens/logout",
        headers={
            "Authorization": f"Bearer {screen_credential}",
            "X-Admin-Session": other_session_token,
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "EXPIRED_SESSION"
    integration_session.expire_all()
    stored_credential = await integration_session.get(ScreenCredentialModel, credential.id)
    assert stored_credential is not None and stored_credential.revoked_at is None
