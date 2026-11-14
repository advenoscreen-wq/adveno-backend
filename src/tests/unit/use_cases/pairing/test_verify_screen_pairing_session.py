"""Unit tests for authenticated pairing session verification."""

import hashlib
from datetime import timedelta
from unittest.mock import Mock

import pytest

from application.exceptions.pairing import PairingSessionNotFoundError
from application.use_cases.pairing.commands import VerifyScreenPairingSessionCommand
from application.use_cases.pairing.verify_screen_pairing_session_use_case import (
    VerifyScreenPairingSessionUseCase,
)
from domain import ScreenPairingSession
from domain.entities.common import utc_now
from domain.value_object import PairingSessionStatus, PairingType


@pytest.mark.asyncio
async def test_verify_pairing_session_returns_session_details(
    verify_screen_pairing_session_use_case: VerifyScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
) -> None:
    pairing_token = "valid-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    pairing_session_repo.get_by_token_hash.return_value = session

    result = await verify_screen_pairing_session_use_case(
        VerifyScreenPairingSessionCommand(pairing_token=pairing_token)
    )

    assert result.session_id == session.id
    assert result.status is PairingSessionStatus.PENDING
    assert result.pairing_type is PairingType.NEW_SCREEN
    assert result.screen_id is None
    assert result.screen_exists is False
    assert result.expires_at == session.expires_at
    assert result.created_at == session.created_at


@pytest.mark.asyncio
async def test_verify_pairing_session_returns_expired_state(
    verify_screen_pairing_session_use_case: VerifyScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
) -> None:
    pairing_token = "pairing-token"
    token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    session = ScreenPairingSession.create(token_hash, timedelta(minutes=10))
    session.expires_at = utc_now() - timedelta(seconds=1)
    pairing_session_repo.get_by_token_hash.return_value = session

    result = await verify_screen_pairing_session_use_case(
        VerifyScreenPairingSessionCommand(pairing_token=pairing_token)
    )

    assert result.session_id == session.id
    assert result.status is PairingSessionStatus.EXPIRED
    assert result.pairing_type is None
    assert result.screen_id is None
    assert not result.screen_exists
    pairing_session_repo.get_by_token_hash.assert_awaited_once_with(token_hash)


@pytest.mark.asyncio
async def test_verify_pairing_session_rejects_unknown_session(
    verify_screen_pairing_session_use_case: VerifyScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
) -> None:
    pairing_session_repo.get_by_token_hash.return_value = None
    with pytest.raises(PairingSessionNotFoundError):
        await verify_screen_pairing_session_use_case(
            VerifyScreenPairingSessionCommand(pairing_token="unknown-token")
        )
