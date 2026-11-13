"""Unit tests for authenticated pairing session verification."""

import hashlib
from datetime import timedelta
from typing import Any

import pytest

from application.exceptions.pairing import PairingSessionNotFoundError
from application.use_cases.pairing.commands import VerifyScreenPairingSessionCommand
from application.use_cases.pairing.verify_screen_pairing_session_use_case import (
    VerifyScreenPairingSessionUseCase,
)
from domain import ScreenPairingSession
from domain.entities.common import utc_now
from domain.value_object import PairingSessionStatus


@pytest.mark.asyncio
async def test_verify_pairing_session_returns_expired_state(
    verify_screen_pairing_session_use_case: VerifyScreenPairingSessionUseCase,
    fake_screen_pairing_session_repository: Any,
) -> None:
    pairing_token = "pairing-token"
    token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    session = ScreenPairingSession.create(token_hash, timedelta(minutes=10))
    session.expires_at = utc_now() - timedelta(seconds=1)
    await fake_screen_pairing_session_repository.save(session)

    result = await verify_screen_pairing_session_use_case(
        VerifyScreenPairingSessionCommand(pairing_token=pairing_token)
    )

    assert result.session_id == session.id
    assert result.status is PairingSessionStatus.EXPIRED
    assert result.pairing_type is None
    assert result.screen_id is None
    assert not result.screen_exists


@pytest.mark.asyncio
async def test_verify_pairing_session_rejects_unknown_session(
    verify_screen_pairing_session_use_case: VerifyScreenPairingSessionUseCase,
) -> None:
    with pytest.raises(PairingSessionNotFoundError):
        await verify_screen_pairing_session_use_case(
            VerifyScreenPairingSessionCommand(pairing_token="unknown-token")
        )
