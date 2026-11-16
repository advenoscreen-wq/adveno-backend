"""Unit tests for paired screen credential issuance."""

import hashlib
from datetime import timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.exceptions.pairing import (
    PairingSessionExpiredError,
    PairingSessionNotFoundError,
    PairingSessionNotPairedError,
)
from application.use_cases.pairing.commands import IssuePairedScreenCredentialCommand
from application.use_cases.pairing.issue_paired_screen_credential_use_case import (
    IssuePairedScreenCredentialUseCase,
)
from domain import ScreenCredential, ScreenPairingSession
from domain.entities.common import utc_now
from domain.value_object import PairingSessionStatus, PairingType


def _connecting_reconnect_session(token: str) -> ScreenPairingSession:
    session = ScreenPairingSession.create(
        hashlib.sha256(token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    session.mark_as_connecting(screen_id=uuid4())
    return session


@pytest.mark.asyncio
async def test_issue_credential_revokes_old_credential_and_completes_reconnect(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "credential-pairing-token"
    session = _connecting_reconnect_session(token)
    old_credential = ScreenCredential(
        screen_id=session.screen_id,
        credential_hash="old-credential-hash",
    )
    pairing_session_repo.get_by_id.return_value = session
    screen_credential_repo.get_active_credential_by_screen.return_value = old_credential

    result = await issue_paired_screen_credential_use_case(
        IssuePairedScreenCredentialCommand(session.id, token)
    )

    assert result.screen_id == session.screen_id
    assert session.status is PairingSessionStatus.PAIRED
    assert session.paired_at is not None
    assert old_credential.revoked_at is not None
    screen_credential_repo.update.assert_awaited_once_with(old_credential)
    stored = screen_credential_repo.save.await_args.args[0]
    assert stored.credential_hash == hashlib.sha256(result.credential.encode()).hexdigest()
    assert result.credential != stored.credential_hash
    pairing_session_repo.update.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_issue_credential_completes_reconnect_without_old_credential(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "first-reconnect-credential"
    session = _connecting_reconnect_session(token)
    pairing_session_repo.get_by_id.return_value = session
    screen_credential_repo.get_active_credential_by_screen.return_value = None

    await issue_paired_screen_credential_use_case(
        IssuePairedScreenCredentialCommand(session.id, token)
    )

    assert session.status is PairingSessionStatus.PAIRED
    assert session.paired_at is not None
    screen_credential_repo.update.assert_not_awaited()
    screen_credential_repo.save.assert_awaited_once()
    pairing_session_repo.update.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_issue_credential_rejects_expired_connecting_session(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "expired-reconnect"
    session = _connecting_reconnect_session(token)
    session.expires_at = utc_now() - timedelta(seconds=1)
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingSessionExpiredError):
        await issue_paired_screen_credential_use_case(
            IssuePairedScreenCredentialCommand(session.id, token)
        )

    screen_credential_repo.save.assert_not_awaited()
    pairing_session_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_issue_credential_rejects_pending_session(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "pending-reconnect"
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
async def test_issue_credential_rejects_unknown_session(
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
async def test_issue_credential_rejects_wrong_pairing_token(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    session = _connecting_reconnect_session("actual-token")
    pairing_session_repo.get_by_id.return_value = session

    with pytest.raises(PairingSessionNotFoundError):
        await issue_paired_screen_credential_use_case(
            IssuePairedScreenCredentialCommand(session.id, "wrong-token")
        )

    screen_credential_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_issue_credential_rotation_keeps_completed_status(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
) -> None:
    token = "rotate-completed-credential"
    session = _connecting_reconnect_session(token)
    session.mark_as_paired()
    pairing_session_repo.get_by_id.return_value = session
    screen_credential_repo.get_active_credential_by_screen.return_value = None

    await issue_paired_screen_credential_use_case(
        IssuePairedScreenCredentialCommand(session.id, token)
    )

    assert session.status is PairingSessionStatus.PAIRED
    pairing_session_repo.update.assert_not_awaited()
    screen_credential_repo.save.assert_awaited_once()
