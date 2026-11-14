"""Unit tests for completion checks and paired credential delivery."""

import hashlib
from datetime import timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.exceptions.pairing import (
    PairingSessionNotFoundError,
    PairingSessionNotPairedError,
)
from application.use_cases.pairing.check_pairing_completion_use_case import (
    CheckPairingCompletionUseCase,
)
from application.use_cases.pairing.commands import (
    CheckPairingCompletionCommand,
    IssuePairedScreenCredentialCommand,
)
from application.use_cases.pairing.issue_paired_screen_credential_use_case import (
    IssuePairedScreenCredentialUseCase,
)
from domain import ScreenCredential, ScreenPairingSession
from domain.value_object import PairingSessionStatus, PairingType


@pytest.mark.asyncio
async def test_pending_pairing_session_is_incomplete(
    check_pairing_completion_use_case: CheckPairingCompletionUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    pairing_token = "completion-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    pairing_session_repo.get_by_token_hash.return_value = session
    screen_credential_repo.get_active_credential_by_screen.return_value = None

    result = await check_pairing_completion_use_case(
        CheckPairingCompletionCommand(pairing_token=pairing_token)
    )
    assert result.status is PairingSessionStatus.PENDING
    assert result.screen_id is None
    assert not result.completed
    screen_credential_repo.get_active_credential_by_screen.assert_not_awaited()


@pytest.mark.asyncio
async def test_paired_session_without_screen_is_incomplete(
    check_pairing_completion_use_case: CheckPairingCompletionUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "paired-without-screen"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_paired()
    pairing_session_repo.get_by_token_hash.return_value = session

    result = await check_pairing_completion_use_case(
        CheckPairingCompletionCommand(pairing_token=token)
    )

    assert result.status is PairingSessionStatus.PAIRED
    assert result.paired_at is not None
    assert result.screen_id is None
    assert not result.completed
    screen_credential_repo.get_active_credential_by_screen.assert_not_awaited()


@pytest.mark.asyncio
async def test_paired_session_without_active_credential_is_incomplete(
    check_pairing_completion_use_case: CheckPairingCompletionUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "paired-without-credential"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_paired()
    session.assign_new_screen(uuid4())
    pairing_session_repo.get_by_token_hash.return_value = session
    screen_credential_repo.get_active_credential_by_screen.return_value = None

    result = await check_pairing_completion_use_case(
        CheckPairingCompletionCommand(pairing_token=token)
    )

    assert not result.completed
    screen_credential_repo.get_active_credential_by_screen.assert_awaited_once_with(
        session.screen_id
    )


@pytest.mark.asyncio
async def test_paired_session_with_active_credential_is_complete(
    check_pairing_completion_use_case: CheckPairingCompletionUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "complete-pairing"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_paired()
    screen_id = uuid4()
    session.assign_new_screen(screen_id)
    pairing_session_repo.get_by_token_hash.return_value = session
    screen_credential_repo.get_active_credential_by_screen.return_value = ScreenCredential(
        screen_id=screen_id,
        credential_hash="active-hash",
    )

    result = await check_pairing_completion_use_case(
        CheckPairingCompletionCommand(pairing_token=token)
    )

    assert result.completed
    assert result.screen_id == screen_id


@pytest.mark.asyncio
async def test_completion_check_rejects_unknown_pairing_token(
    check_pairing_completion_use_case: CheckPairingCompletionUseCase,
    pairing_session_repo: Mock,
) -> None:
    pairing_session_repo.get_by_token_hash.return_value = None

    with pytest.raises(PairingSessionNotFoundError):
        await check_pairing_completion_use_case(
            CheckPairingCompletionCommand(pairing_token="unknown-token")
        )


@pytest.mark.asyncio
async def test_credential_endpoint_replaces_active_credential_and_returns_raw_secret(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    pairing_token = "credential-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
        screen_id=uuid4(),
    )
    session.mark_as_paired(screen_id=session.screen_id)
    pairing_session_repo.get_by_id.return_value = session
    old_credential = ScreenCredential(
        screen_id=session.screen_id,
        credential_hash="old-credential-hash",
    )
    screen_credential_repo.get_active_credential_by_screen.return_value = old_credential

    result = await issue_paired_screen_credential_use_case(
        IssuePairedScreenCredentialCommand(
            session_id=session.id,
            pairing_token=pairing_token,
        )
    )

    assert result.screen_id == session.screen_id
    assert old_credential.revoked_at is not None
    screen_credential_repo.update.assert_awaited_once_with(old_credential)
    screen_credential_repo.save.assert_awaited_once()
    stored_credential = screen_credential_repo.save.await_args.args[0]
    assert (
        stored_credential.credential_hash
        == hashlib.sha256(result.credential.encode("utf-8")).hexdigest()
    )
    assert result.credential != stored_credential.credential_hash


@pytest.mark.asyncio
async def test_credential_endpoint_creates_first_credential_after_reconnect_approval(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    pairing_token = "missing-credential-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
        screen_id=uuid4(),
    )
    session.mark_as_paired(screen_id=session.screen_id)
    pairing_session_repo.get_by_id.return_value = session
    screen_credential_repo.get_active_credential_by_screen.return_value = None

    result = await issue_paired_screen_credential_use_case(
        IssuePairedScreenCredentialCommand(
            session_id=session.id,
            pairing_token=pairing_token,
        )
    )
    screen_credential_repo.update.assert_not_awaited()
    screen_credential_repo.save.assert_awaited_once()
    stored_credential = screen_credential_repo.save.await_args.args[0]
    assert (
        stored_credential.credential_hash
        == hashlib.sha256(result.credential.encode("utf-8")).hexdigest()
    )


@pytest.mark.asyncio
async def test_credential_endpoint_rejects_unknown_session(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    pairing_session_repo.get_by_id.return_value = None

    with pytest.raises(PairingSessionNotFoundError):
        await issue_paired_screen_credential_use_case(
            IssuePairedScreenCredentialCommand(uuid4(), "unknown-token")
        )

    screen_credential_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_credential_endpoint_rejects_unpaired_session(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "not-paired-yet"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingSessionNotPairedError):
        await issue_paired_screen_credential_use_case(
            IssuePairedScreenCredentialCommand(session.id, token)
        )

    screen_credential_repo.get_active_credential_by_screen.assert_not_awaited()
    screen_credential_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_credential_endpoint_rejects_wrong_pairing_token(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    actual_token = "actual-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(actual_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
        screen_id=uuid4(),
    )
    session.mark_as_paired(screen_id=session.screen_id)
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingSessionNotFoundError):
        await issue_paired_screen_credential_use_case(
            IssuePairedScreenCredentialCommand(session.id, "wrong-token")
        )

    screen_credential_repo.get_active_credential_by_screen.assert_not_awaited()
    screen_credential_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_credential_endpoint_rejects_paired_session_without_screen(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "paired-without-screen"
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_paired()
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingSessionNotPairedError):
        await issue_paired_screen_credential_use_case(
            IssuePairedScreenCredentialCommand(session.id, token)
        )

    screen_credential_repo.get_active_credential_by_screen.assert_not_awaited()
