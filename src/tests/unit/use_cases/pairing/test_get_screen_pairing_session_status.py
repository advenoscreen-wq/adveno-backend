"""Unit tests for pairing status lookup by session ID and token."""

import hashlib
from datetime import timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.exceptions.pairing import PairingSessionNotFoundError
from application.use_cases.pairing.commands import GetScreenPairingSessionStatusCommand
from application.use_cases.pairing.get_screen_pairing_session_status_use_case import (
    GetScreenPairingSessionStatusUseCase,
)
from domain import ScreenPairingSession
from domain.entities.common import utc_now
from domain.value_object import PairingSessionStatus, PairingType


@pytest.mark.asyncio
async def test_status_lookup_returns_paired_status_for_matching_token(
    get_screen_pairing_session_status_use_case: GetScreenPairingSessionStatusUseCase,
    pairing_session_repo: Mock,
) -> None:
    pairing_token = "status-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_paired()
    pairing_session_repo.get_by_id.return_value = session

    result = await get_screen_pairing_session_status_use_case(
        GetScreenPairingSessionStatusCommand(session.id, pairing_token)
    )

    assert result.status is PairingSessionStatus.PAIRED
    pairing_session_repo.get_by_id.assert_awaited_once_with(session.id)


@pytest.mark.asyncio
async def test_status_lookup_reports_expired_pending_session(
    get_screen_pairing_session_status_use_case: GetScreenPairingSessionStatusUseCase,
    pairing_session_repo: Mock,
) -> None:
    pairing_token = "expired-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(), timedelta(minutes=10)
    )
    session.expires_at = utc_now() - timedelta(seconds=1)
    pairing_session_repo.get_by_id.return_value = session

    result = await get_screen_pairing_session_status_use_case(
        GetScreenPairingSessionStatusCommand(session.id, pairing_token)
    )

    assert result.status is PairingSessionStatus.EXPIRED


@pytest.mark.asyncio
@pytest.mark.parametrize("stored_session", [None, "different-token"])
async def test_status_lookup_rejects_missing_session_or_wrong_token(
    get_screen_pairing_session_status_use_case: GetScreenPairingSessionStatusUseCase,
    pairing_session_repo: Mock,
    stored_session: ScreenPairingSession | None | str,
) -> None:
    pairing_token = "supplied-token"
    if stored_session == "different-token":
        stored_session = ScreenPairingSession.create(
            hashlib.sha256(b"actual-token").hexdigest(), timedelta(minutes=10)
        )
    pairing_session_repo.get_by_id.return_value = stored_session
    session_id = stored_session.id if isinstance(stored_session, ScreenPairingSession) else uuid4()

    with pytest.raises(PairingSessionNotFoundError):
        await get_screen_pairing_session_status_use_case(
            GetScreenPairingSessionStatusCommand(session_id, pairing_token)
        )
