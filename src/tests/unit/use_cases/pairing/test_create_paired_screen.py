"""Unit tests for screen creation from a paired session."""

import hashlib
from datetime import timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.exceptions.pairing import (
    PairingApprovalValidationError,
    PairingOwnerNotSetError,
    PairingScreenAlreadyCreatedError,
    PairingSessionExpiredError,
    PairingSessionNotFoundError,
    PairingSessionNotPairedError,
)
from application.use_cases.pairing.commands import CreatePairedScreenCommand
from application.use_cases.pairing.create_paired_screen_use_case import (
    CreatePairedScreenUseCase,
)
from domain import ScreenPairingSession
from domain.value_object import PairingSessionStatus, PairingType


@pytest.mark.asyncio
async def test_creates_screen_and_assigns_it_to_paired_new_screen_session(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_sync_state_repo: Mock,
) -> None:
    pairing_token = "tv-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    user_id = uuid4()
    session.mark_as_connecting(approved_by_user_id=user_id)
    pairing_session_repo.get_by_id.return_value = session

    result = await create_paired_screen_use_case(
        CreatePairedScreenCommand(
            session_id=session.id,
            pairing_token=pairing_token,
            name="Lobby TV",
            device_model="Model X",
            app_version="1.2.3",
        )
    )

    screen = screen_repo.save.await_args.args[0]
    assert screen.user_id == user_id
    assert screen.name == "Lobby TV"
    assert screen.device_model == "Model X"
    assert screen.app_version == "1.2.3"
    assert result.screen_code == screen.screen_code
    assert session.screen_id == screen.id
    assert session.status is PairingSessionStatus.PAIRED
    assert session.paired_at is not None
    screen_credential_repo.save.assert_awaited_once()
    screen_sync_state_repo.save.assert_awaited_once()
    sync_state = screen_sync_state_repo.save.await_args.args[0]
    assert sync_state.screen_id == screen.id
    assert sync_state.desired_revision == 0
    assert sync_state.applied_revision == 0
    stored_credential = screen_credential_repo.save.await_args.args[0]
    assert (
        stored_credential.credential_hash
        == hashlib.sha256(result.credential.encode("utf-8")).hexdigest()
    )
    assert result.credential != stored_credential.credential_hash
    pairing_session_repo.update.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_does_not_create_second_screen_for_pairing_session_with_screen_id(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
) -> None:
    token = "already-created-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_connecting()
    session.assign_new_screen(uuid4())
    session.mark_as_paired()
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingScreenAlreadyCreatedError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(session.id, token, "Duplicate TV")
        )

    screen_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_does_not_create_screen_when_approved_owner_was_not_recorded(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
) -> None:
    token = "ownerless-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_connecting()
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingOwnerNotSetError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(session_id=session.id, pairing_token=token, name="TV")
        )

    screen_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_does_not_create_screen_before_session_is_paired(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    pairing_token = "pending-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingSessionNotPairedError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(
                session_id=session.id,
                pairing_token=pairing_token,
                name="Lobby TV",
            )
        )

    screen_repo.save.assert_not_awaited()
    screen_credential_repo.save.assert_not_awaited()
    pairing_session_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejects_session_id_and_pairing_token_that_do_not_match(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    valid_token = "valid-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(valid_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_connecting()
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingSessionNotFoundError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(
                session_id=session.id,
                pairing_token="different-token",
                name="Lobby TV",
            )
        )

    screen_repo.save.assert_not_awaited()
    screen_credential_repo.save.assert_not_awaited()
    pairing_session_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejects_unknown_pairing_session(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
) -> None:
    pairing_session_repo.get_by_id.return_value = None

    with pytest.raises(PairingSessionNotFoundError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(
                session_id=uuid4(),
                pairing_token="unknown-token",
                name="Lobby TV",
            )
        )

    screen_repo.save.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("expired_by_status", [True, False])
async def test_does_not_create_screen_for_expired_session(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
    expired_by_status: bool,
) -> None:
    token = "expired-new-screen-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    if expired_by_status:
        session.status = PairingSessionStatus.EXPIRED
    else:
        session.expires_at = session.created_at - timedelta(seconds=1)
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingSessionExpiredError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(session.id, token, "Lobby TV")
        )

    screen_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejects_reconnect_session_for_new_screen_creation(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    pairing_session_repo: Mock,
    screen_repo: Mock,
) -> None:
    token = "reconnect-token"
    existing_screen_id = uuid4()
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    session.mark_as_connecting(screen_id=existing_screen_id, approved_by_user_id=uuid4())
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingApprovalValidationError) as error:
        await create_paired_screen_use_case(CreatePairedScreenCommand(session.id, token, "New TV"))

    assert error.value.code == "NEW_SCREEN_PAIRING_REQUIRED"
    screen_repo.save.assert_not_awaited()
