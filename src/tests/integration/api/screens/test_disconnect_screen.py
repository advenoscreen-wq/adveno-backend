"""Integration tests for disconnecting a screen without deleting its data."""

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
    SqlAlchemyPlaylistRepository,
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
)
from adapters.repositories.screen_credential_repository import (
    SqlAlchemyScreenCredentialRepository,
)
from domain import Playlist, Screen, ScreenCredential, ScreenPlaylistAssignment

pytestmark = pytest.mark.integration

USER_ID = UUID("00000000-0000-0000-0000-000000000099")
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


async def test_disconnect_screen_revokes_credential_and_preserves_screen_data(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Connected screen")
    )
    credential_repository = SqlAlchemyScreenCredentialRepository(integration_session)
    credential = await credential_repository.save(
        ScreenCredential(screen_id=screen.id, credential_hash=uuid4().hex)
    )
    playlist = await SqlAlchemyPlaylistRepository(integration_session).save(
        Playlist(name="Keep playlist", user_id=USER_ID)
    )
    assignment_repository = SqlAlchemyScreenPlaylistAssignmentRepository(integration_session)
    await assignment_repository.save(
        ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
    )
    await integration_session.commit()

    response = await client.post(
        f"/api/v1/screens/{screen.id}/disconnect",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 204
    persisted_screen = await SqlAlchemyScreenRepository(integration_session).get_by_id(
        screen.id,
        user_id=USER_ID,
    )
    assert persisted_screen is not None
    persisted_credential = await credential_repository.get_by_id(credential.id)
    assert persisted_credential is not None
    assert persisted_credential.revoked_at is not None
    assert await credential_repository.get_active_credential_by_screen(screen.id) is None
    assert len(await assignment_repository.list_by_screen_id(screen.id)) == 1


async def test_disconnect_screen_without_credential_is_idempotent(
    client: httpx.AsyncClient,
    integration_session: AsyncSession,
) -> None:
    screen = await SqlAlchemyScreenRepository(integration_session).save(
        Screen(user_id=USER_ID, name="Already disconnected screen")
    )
    await integration_session.commit()

    response = await client.post(
        f"/api/v1/screens/{screen.id}/disconnect",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 204


async def test_disconnect_screen_returns_not_found_for_unknown_screen(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        f"/api/v1/screens/{uuid4()}/disconnect",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCREEN_NOT_FOUND"


async def test_disconnect_screen_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.post(f"/api/v1/screens/{uuid4()}/disconnect")

    assert response.status_code == 401
