"""Unit tests for PIN-protected screen administration sessions."""

import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import ANY, Mock
from uuid import uuid4

import pytest

from application.exceptions.screen import (
    ExpiredScreenAdminSessionError,
    InvalidScreenAdminPinError,
    ScreenAdminPinRateLimitError,
    ScreenNotFoundError,
)
from application.use_cases.screens.commands import (
    CreateScreenAdminSessionCommand,
    VerifyScreenAdminSessionCommand,
)
from application.use_cases.screens.create_screen_admin_session_use_case import (
    CreateScreenAdminSessionUseCase,
)
from application.use_cases.screens.verify_screen_admin_session_use_case import (
    VerifyScreenAdminSessionUseCase,
)
from domain import Screen, ScreenAdminSession, ScreenCredential


@pytest.mark.asyncio
async def test_create_admin_session_returns_six_digit_pin_and_persists_only_hash(
    create_screen_admin_session_use_case: CreateScreenAdminSessionUseCase,
    screen_repo: Mock,
    screen_admin_session_repo: Mock,
    pin_hasher: Mock,
) -> None:
    owner_id = uuid4()
    screen = Screen(user_id=owner_id, name="Lobby TV")
    screen_repo.get_by_id.return_value = screen

    result = await create_screen_admin_session_use_case(
        CreateScreenAdminSessionCommand(screen_id=screen.id, user_id=owner_id)
    )

    assert len(result.pin) == 6
    assert result.pin.isdigit()
    pin_hasher.hash_pin.assert_awaited_once_with(result.pin)
    screen_admin_session_repo.revoke_pending_by_screen_id.assert_awaited_once_with(
        screen.id, at=ANY
    )
    stored_session = screen_admin_session_repo.save.await_args.args[0]
    assert stored_session.code_hash == "scrypt$mock-hash"
    assert stored_session.code_hash != result.pin
    assert stored_session.token_hash is None
    assert stored_session.expires_at - stored_session.created_at == timedelta(minutes=5)


@pytest.mark.asyncio
async def test_create_admin_session_rejects_screen_not_owned_by_user(
    create_screen_admin_session_use_case: CreateScreenAdminSessionUseCase,
    screen_repo: Mock,
    screen_admin_session_repo: Mock,
) -> None:
    screen_repo.get_by_id.return_value = None

    with pytest.raises(ScreenNotFoundError):
        await create_screen_admin_session_use_case(
            CreateScreenAdminSessionCommand(screen_id=uuid4(), user_id=uuid4())
        )

    screen_admin_session_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_admin_pin_issues_raw_token_and_stores_only_token_hash(
    verify_screen_admin_session_use_case: VerifyScreenAdminSessionUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_admin_session_repo: Mock,
    cache_service: Mock,
    pin_hasher: Mock,
) -> None:
    screen = Screen(user_id=uuid4(), name="Lobby TV")
    raw_screen_credential = "screen-device-credential"
    device_credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(raw_screen_credential.encode()).hexdigest(),
    )
    now = datetime.now(UTC)
    pin_session = ScreenAdminSession(
        screen_id=screen.id,
        code_hash="scrypt$pin-hash",
        created_at=now - timedelta(minutes=1),
        last_activity_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=4),
    )
    screen_repo.get_by_id.return_value = screen
    screen_credential_repo.get_by_hash.return_value = device_credential
    screen_admin_session_repo.get_pending_pin_by_screen_id.return_value = pin_session

    result = await verify_screen_admin_session_use_case(
        credential=raw_screen_credential,
        command=VerifyScreenAdminSessionCommand(pin="012345"),
    )

    assert len(result.session_token) >= 32
    assert pin_session.token_hash == hashlib.sha256(result.session_token.encode()).hexdigest()
    assert pin_session.token_hash != result.session_token
    assert result.expires_at - pin_session.last_activity_at == timedelta(minutes=15)
    pin_hasher.verify_pin.assert_awaited_once_with("scrypt$pin-hash", "012345")
    cache_service.delete.assert_awaited_once_with(f"screen-admin:pin-attempts:{screen.id}")
    screen_admin_session_repo.update.assert_awaited_once_with(pin_session)


@pytest.mark.asyncio
async def test_verify_admin_pin_rejects_incorrect_pin_and_rate_limits_attempt(
    verify_screen_admin_session_use_case: VerifyScreenAdminSessionUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_admin_session_repo: Mock,
    cache_service: Mock,
    pin_hasher: Mock,
) -> None:
    screen = Screen(user_id=uuid4(), name="Lobby TV")
    raw_screen_credential = "screen-device-credential"
    screen_credential_repo.get_by_hash.return_value = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(raw_screen_credential.encode()).hexdigest(),
    )
    screen_repo.get_by_id.return_value = screen
    screen_admin_session_repo.get_pending_pin_by_screen_id.return_value = ScreenAdminSession(
        screen_id=screen.id,
        code_hash="scrypt$pin-hash",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    pin_hasher.verify_pin.return_value = False

    with pytest.raises(InvalidScreenAdminPinError):
        await verify_screen_admin_session_use_case(
            credential=raw_screen_credential,
            command=VerifyScreenAdminSessionCommand(pin="999999"),
        )

    cache_service.increment_with_ttl.assert_awaited_once()
    screen_admin_session_repo.update.assert_not_awaited()

    cache_service.increment_with_ttl.return_value = 6
    with pytest.raises(ScreenAdminPinRateLimitError):
        await verify_screen_admin_session_use_case(
            credential=raw_screen_credential,
            command=VerifyScreenAdminSessionCommand(pin="999999"),
        )

    pin_hasher.verify_pin.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_admin_pin_rejects_expired_or_revoked_challenge_before_hash_check(
    verify_screen_admin_session_use_case: VerifyScreenAdminSessionUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_admin_session_repo: Mock,
    pin_hasher: Mock,
) -> None:
    screen = Screen(user_id=uuid4(), name="Lobby TV")
    credential = "screen-device-credential"
    screen_repo.get_by_id.return_value = screen
    screen_credential_repo.get_by_hash.return_value = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(credential.encode()).hexdigest(),
    )
    expired_session = ScreenAdminSession(
        screen_id=screen.id,
        code_hash="scrypt$pin-hash",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    screen_admin_session_repo.get_pending_pin_by_screen_id.return_value = expired_session

    with pytest.raises(ExpiredScreenAdminSessionError):
        await verify_screen_admin_session_use_case(
            credential=credential,
            command=VerifyScreenAdminSessionCommand(pin="012345"),
        )

    pin_hasher.verify_pin.assert_not_awaited()
