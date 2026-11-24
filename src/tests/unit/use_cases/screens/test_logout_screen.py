"""Unit tests for protected screen-device logout."""

import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.use_cases.screens.logout_screen_use_case import LogoutScreenUseCase
from application.use_cases.screens.results import ProtectedScreenAdminSession
from domain import Screen, ScreenAdminSession, ScreenCredential


@pytest.mark.asyncio
async def test_logout_revokes_authenticated_credential_and_admin_session(
    logout_screen_use_case: LogoutScreenUseCase,
    screen_credential_repo: Mock,
    screen_admin_session_repo: Mock,
) -> None:
    now = datetime.now(UTC)
    screen = Screen(user_id=uuid4(), name="Lobby TV")
    credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(b"screen-secret").hexdigest(),
    )
    admin_session = ScreenAdminSession(
        screen_id=screen.id,
        code_hash="scrypt$pin-hash",
        token_hash="hashed-session-token",
        created_at=now - timedelta(minutes=1),
        last_activity_at=now,
        expires_at=now + timedelta(minutes=14),
    )

    await logout_screen_use_case(
        ProtectedScreenAdminSession(
            screen=screen,
            credential=credential,
            admin_session=admin_session,
        )
    )

    assert credential.revoked_at is not None
    assert admin_session.revoked_at is not None
    screen_credential_repo.update.assert_awaited_once_with(credential)
    screen_admin_session_repo.update.assert_awaited_once_with(admin_session)
