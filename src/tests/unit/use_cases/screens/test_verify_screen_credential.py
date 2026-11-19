"""Unit tests for screen credential verification."""

import hashlib
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.exceptions.screen import ScreenDeviceNotFoundError
from application.use_cases.screens.verify_screen_credential_use_case import (
    VerifyScreenCredentialUseCase,
)
from domain import Screen, ScreenCredential


@pytest.mark.asyncio
async def test_verification_accepts_an_active_device_credential(
    verify_screen_credential_use_case: VerifyScreenCredentialUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    raw_credential = "screen-credential"
    screen = Screen(user_id=uuid4(), name="Lobby TV")
    credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
    )
    screen_repo.get_by_id.return_value = screen
    screen_credential_repo.get_by_hash.return_value = credential

    await verify_screen_credential_use_case(credential=raw_credential)

    assert screen.last_seen_at is not None
    assert credential.last_used_at is not None
    screen_repo.update.assert_awaited_once_with(screen)
    screen_credential_repo.update.assert_awaited_once_with(credential)


@pytest.mark.asyncio
async def test_verification_rejects_an_unknown_device_credential(
    verify_screen_credential_use_case: VerifyScreenCredentialUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    screen_credential_repo.get_by_hash.return_value = None

    with pytest.raises(ScreenDeviceNotFoundError):
        await verify_screen_credential_use_case(credential="unknown-credential")

    screen_repo.get_by_id.assert_not_awaited()
