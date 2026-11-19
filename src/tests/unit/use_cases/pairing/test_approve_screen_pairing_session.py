"""Unit tests for pairing approval."""

import hashlib
from datetime import timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.exceptions.pairing import (
    PairingApprovalValidationError,
    PairingScreenNotEligibleError,
    PairingScreenNotFoundError,
    PairingSessionAlreadyCompletedError,
    PairingSessionExpiredError,
    PairingSessionNotFoundError,
)
from application.use_cases.pairing.approve_screen_pairing_session_use_case import (
    ApproveScreenPairingSessionUseCase,
)
from application.use_cases.pairing.commands import ApproveScreenPairingSessionCommand
from domain import Screen, ScreenCredential, ScreenPairingSession
from domain.value_object import PairingSessionStatus, PairingType, ScreenStatus


@pytest.mark.asyncio
async def test_new_screen_approval_marks_connecting_without_creating_screen(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    pairing_token = "new-screen-token"
    token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    session = ScreenPairingSession.create(
        token_hash,
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    pairing_session_repo.get_by_token_hash.return_value = session

    user_id = uuid4()
    result = await approve_screen_pairing_session_use_case(
        ApproveScreenPairingSessionCommand(
            pairing_token=pairing_token,
            user_id=user_id,
        )
    )

    assert result.status is PairingSessionStatus.CONNECTING
    assert result.paired_at is None
    assert result.screen_id is None
    assert session.paired_at is None
    assert session.approved_by_user_id == user_id
    screen_repo.save.assert_not_awaited()
    screen_credential_repo.get_active_credential_by_screen.assert_not_awaited()
    screen_credential_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_reconnect_approval_marks_connecting_and_revokes_active_credential(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    user_id = uuid4()
    screen = Screen(user_id=user_id, name="Lobby")
    screen_repo.get_by_id.return_value = screen
    old_credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash="old-credential-hash",
    )
    screen_credential_repo.get_active_credential_by_screen.return_value = old_credential
    pairing_token = "reconnect-token"
    token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    session = ScreenPairingSession.create(
        token_hash,
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    pairing_session_repo.get_by_token_hash.return_value = session

    result = await approve_screen_pairing_session_use_case(
        ApproveScreenPairingSessionCommand(
            pairing_token=pairing_token,
            user_id=user_id,
            screen_id=screen.id,
        )
    )

    assert result.status is PairingSessionStatus.CONNECTING
    assert result.paired_at is None
    assert result.screen_id == screen.id
    assert session.screen_id == screen.id
    screen_repo.get_by_id.assert_awaited_once_with(screen.id, user_id=user_id)
    assert old_credential.revoked_at is not None
    screen_credential_repo.update.assert_awaited_once_with(old_credential)
    screen_credential_repo.save.assert_not_awaited()
    pairing_session_repo.update.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_reconnect_approval_rejects_screen_owned_by_another_user(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    screen = Screen(user_id=uuid4(), name="Other owner's screen")
    screen_repo.get_by_id.return_value = None
    pairing_token = "reconnect-token"
    token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    session = ScreenPairingSession.create(
        token_hash,
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    pairing_session_repo.get_by_token_hash.return_value = session

    with pytest.raises(PairingScreenNotFoundError):
        await approve_screen_pairing_session_use_case(
            ApproveScreenPairingSessionCommand(
                pairing_token=pairing_token,
                user_id=uuid4(),
                screen_id=screen.id,
            )
        )

    assert session.status is PairingSessionStatus.PENDING
    assert session.paired_at is None
    screen_credential_repo.get_active_credential_by_screen.assert_not_awaited()
    screen_credential_repo.update.assert_not_awaited()
    screen_credential_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_approval_rejects_unknown_pairing_token(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
) -> None:
    pairing_session_repo.get_by_token_hash.return_value = None

    with pytest.raises(PairingSessionNotFoundError):
        await approve_screen_pairing_session_use_case(
            ApproveScreenPairingSessionCommand(
                pairing_token="unknown-token",
                user_id=uuid4(),
            )
        )

    pairing_session_repo.update.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("expired_by_status", [True, False])
async def test_approval_rejects_expired_session(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
    expired_by_status: bool,
) -> None:
    token = "expired-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    if expired_by_status:
        session.status = PairingSessionStatus.EXPIRED
    else:
        session.expires_at = session.created_at - timedelta(seconds=1)
    pairing_session_repo.get_by_token_hash.return_value = session

    with pytest.raises(PairingSessionExpiredError):
        await approve_screen_pairing_session_use_case(
            ApproveScreenPairingSessionCommand(token, uuid4())
        )

    pairing_session_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_approval_rejects_already_paired_session(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
) -> None:
    token = "already-paired-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_connecting()
    session.assign_new_screen(uuid4())
    session.mark_as_paired()
    pairing_session_repo.get_by_token_hash.return_value = session

    with pytest.raises(PairingSessionAlreadyCompletedError):
        await approve_screen_pairing_session_use_case(
            ApproveScreenPairingSessionCommand(token, uuid4())
        )


@pytest.mark.asyncio
async def test_approval_rejects_session_without_pairing_type(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
) -> None:
    token = "unselected-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
    )
    pairing_session_repo.get_by_token_hash.return_value = session

    with pytest.raises(PairingApprovalValidationError, match="Pairing type") as error:
        await approve_screen_pairing_session_use_case(
            ApproveScreenPairingSessionCommand(token, uuid4())
        )

    assert error.value.code == "PAIRING_TYPE_REQUIRED"


@pytest.mark.asyncio
async def test_new_screen_approval_rejects_existing_screen_id(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
) -> None:
    token = "new-screen-token-with-id"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    pairing_session_repo.get_by_token_hash.return_value = session

    with pytest.raises(PairingApprovalValidationError) as error:
        await approve_screen_pairing_session_use_case(
            ApproveScreenPairingSessionCommand(token, uuid4(), screen_id=uuid4())
        )

    assert error.value.code == "SCREEN_ID_NOT_ALLOWED"
    screen_repo.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_reconnect_approval_requires_screen_id(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
) -> None:
    token = "reconnect-without-screen"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    pairing_session_repo.get_by_token_hash.return_value = session

    with pytest.raises(PairingApprovalValidationError) as error:
        await approve_screen_pairing_session_use_case(
            ApproveScreenPairingSessionCommand(token, uuid4())
        )

    assert error.value.code == "SCREEN_ID_REQUIRED"
    screen_repo.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_reconnect_approval_rejects_inactive_screen(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "inactive-screen-token"
    user_id = uuid4()
    screen = Screen(user_id=user_id, name="Inactive display", status=ScreenStatus.INACTIVE)
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    pairing_session_repo.get_by_token_hash.return_value = session
    screen_repo.get_by_id.return_value = screen

    with pytest.raises(PairingScreenNotEligibleError):
        await approve_screen_pairing_session_use_case(
            ApproveScreenPairingSessionCommand(token, user_id, screen_id=screen.id)
        )

    screen_credential_repo.get_active_credential_by_screen.assert_not_awaited()
    pairing_session_repo.update.assert_not_awaited()
