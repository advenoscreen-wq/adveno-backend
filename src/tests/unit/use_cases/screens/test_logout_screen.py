"""Unit tests for screen-device logout."""

import hashlib
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.exceptions.screen import ScreenDeviceNotFoundError, ScreenDisconnectedError
from application.use_cases.screens.logout_screen_use_case import LogoutScreenUseCase
from domain import Screen, ScreenCredential
from domain.value_object import ScreenStatus


@pytest.mark.asyncio
async def test_logout_revokes_authenticated_credential(
    logout_screen_use_case: LogoutScreenUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    raw_credential = "screen-secret"
    screen = Screen(user_id=uuid4(), name="Lobby TV")
    device_credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
    )
    screen_repo.get_by_id.return_value = screen
    screen_credential_repo.get_by_hash.return_value = device_credential

    await logout_screen_use_case(credential=raw_credential)

    assert device_credential.revoked_at is not None
    screen_repo.update.assert_awaited_once_with(screen)
    screen_credential_repo.update.assert_awaited_once_with(device_credential)


@pytest.mark.asyncio
async def test_logout_returns_not_found_for_unknown_credential(
    logout_screen_use_case: LogoutScreenUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    screen_credential_repo.get_by_hash.return_value = None

    with pytest.raises(ScreenDeviceNotFoundError):
        await logout_screen_use_case(credential="unknown")

    screen_repo.get_by_id.assert_not_awaited()
    screen_credential_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_rejects_inactive_screen_without_revoking_credential(
    logout_screen_use_case: LogoutScreenUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    screen = Screen(user_id=uuid4(), name="Inactive TV", status=ScreenStatus.INACTIVE)
    device_credential = ScreenCredential(screen_id=screen.id, credential_hash="stored-hash")
    screen_repo.get_by_id.return_value = screen
    screen_credential_repo.get_by_hash.return_value = device_credential

    with pytest.raises(ScreenDisconnectedError):
        await logout_screen_use_case(credential="screen-secret")

    screen_repo.update.assert_not_awaited()
    screen_credential_repo.update.assert_not_awaited()
