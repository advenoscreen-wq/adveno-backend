"""Unit tests for creating screen pairing sessions."""

import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from application.use_cases.pairing.commands import CreateScreenPairingSessionCommand
from application.use_cases.pairing.create_screen_pairing_session_use_case import (
    CreateScreenPairingSessionUseCase,
)
from domain.value_object import PairingSessionStatus, PairingType


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pairing_type",
    [PairingType.NEW_SCREEN, PairingType.RECONNECT_EXISTING],
)
async def test_create_pairing_session_persists_only_hash_and_returns_raw_token(
    create_screen_pairing_session_use_case: CreateScreenPairingSessionUseCase,
    pairing_session_repo: Mock,
    pairing_type: PairingType,
) -> None:
    started_at = datetime.now(UTC)

    result = await create_screen_pairing_session_use_case(
        CreateScreenPairingSessionCommand(pairing_type=pairing_type)
    )

    finished_at = datetime.now(UTC)
    pairing_session_repo.save.assert_awaited_once()
    stored = pairing_session_repo.save.await_args.args[0]
    expected_hash = hashlib.sha256(result.pairing_token.encode("utf-8")).hexdigest()

    assert result.pairing_token
    assert stored.token_hash == expected_hash
    assert stored.token_hash != result.pairing_token
    assert stored.id == result.session_id
    assert started_at + timedelta(minutes=10) <= result.expires_at
    assert result.expires_at <= finished_at + timedelta(minutes=10)
    assert result.expires_at == stored.expires_at
    assert stored.pairing_type is pairing_type
    assert stored.screen_id is None
    assert stored.status is PairingSessionStatus.PENDING
    assert stored.paired_at is None
