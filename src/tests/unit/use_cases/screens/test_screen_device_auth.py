"""Unit tests for screen-device authentication outcomes."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from application.exceptions.screen import ScreenDeviceNotFoundError, ScreenDisconnectedError
from application.use_cases.screens.screen_device_auth import authenticate_screen_device
from domain import Screen, ScreenCredential
from domain.value_object import ScreenStatus
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository


@pytest.mark.asyncio
async def test_authentication_reports_screen_not_found_for_unknown_device_credential() -> None:
    screen_repository = Mock(spec=ScreenRepository)
    screen_repository.get_by_id = AsyncMock()
    credential_repository = Mock(spec=ScreenCredentialRepository)
    credential_repository.get_by_hash = AsyncMock(return_value=None)

    with pytest.raises(ScreenDeviceNotFoundError):
        await authenticate_screen_device(
            credential="unknown-token",
            screen_repository=screen_repository,
            credential_repository=credential_repository,
        )

    screen_repository.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_authentication_reports_missing_screen_for_known_credential() -> None:
    credential = ScreenCredential(screen_id=uuid4(), credential_hash="stored-hash")
    screen_repository = Mock(spec=ScreenRepository)
    screen_repository.get_by_id = AsyncMock(return_value=None)
    credential_repository = Mock(spec=ScreenCredentialRepository)
    credential_repository.get_by_hash = AsyncMock(return_value=credential)

    with pytest.raises(ScreenDeviceNotFoundError):
        await authenticate_screen_device(
            credential="known-token",
            screen_repository=screen_repository,
            credential_repository=credential_repository,
        )


@pytest.mark.asyncio
async def test_authentication_reports_disconnected_for_inactive_screen() -> None:
    screen = Screen(user_id=uuid4(), name="Inactive TV", status=ScreenStatus.INACTIVE)
    credential = ScreenCredential(screen_id=screen.id, credential_hash="stored-hash")
    screen_repository = Mock(spec=ScreenRepository)
    screen_repository.get_by_id = AsyncMock(return_value=screen)
    credential_repository = Mock(spec=ScreenCredentialRepository)
    credential_repository.get_by_hash = AsyncMock(return_value=credential)

    with pytest.raises(ScreenDisconnectedError):
        await authenticate_screen_device(
            credential="known-token",
            screen_repository=screen_repository,
            credential_repository=credential_repository,
        )

    screen_repository.update.assert_not_awaited()
    credential_repository.update.assert_not_awaited()
