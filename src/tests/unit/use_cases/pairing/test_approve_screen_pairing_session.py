"""Unit tests for pairing approval."""

import hashlib
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest

from application.exceptions.pairing import PairingScreenNotFoundError
from application.use_cases.pairing.approve_screen_pairing_session_use_case import (
    ApproveScreenPairingSessionUseCase,
)
from application.use_cases.pairing.commands import ApproveScreenPairingSessionCommand
from domain import Screen, ScreenCredential, ScreenPairingSession
from domain.value_object import PairingSessionStatus, PairingType


@pytest.mark.asyncio
async def test_new_screen_approval_pairs_session_without_creating_screen(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    pairing_token = "new-screen-token"
    token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    session = ScreenPairingSession.create(
        token_hash,
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    await fake_screen_pairing_session_repository.save(session)

    result = await approve_screen_pairing_session_use_case(
        ApproveScreenPairingSessionCommand(
            pairing_token=pairing_token,
            user_id=uuid4(),
        )
    )

    assert result.status is PairingSessionStatus.PAIRED
    assert result.paired_at is not None
    assert result.screen_id is None
    assert fake_screen_pairing_session_repository.sessions[session.id].paired_at is not None
    assert fake_screen_repository.screens == {}
    assert fake_screen_credential_repository.credentials == {}


@pytest.mark.asyncio
async def test_reconnect_approval_assigns_owned_active_screen(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    user_id = uuid4()
    screen = Screen(user_id=user_id, name="Lobby")
    fake_screen_repository.screens[screen.id] = screen
    old_credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash="old-credential-hash",
    )
    fake_screen_credential_repository.credentials[old_credential.id] = old_credential
    pairing_token = "reconnect-token"
    token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    session = ScreenPairingSession.create(
        token_hash,
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    await fake_screen_pairing_session_repository.save(session)

    result = await approve_screen_pairing_session_use_case(
        ApproveScreenPairingSessionCommand(
            pairing_token=pairing_token,
            user_id=user_id,
            screen_id=screen.id,
        )
    )

    assert result.status is PairingSessionStatus.PAIRED
    assert result.paired_at is not None
    assert result.screen_id == screen.id
    assert fake_screen_repository.screens[screen.id] is screen
    assert old_credential.revoked_at is not None
    active_credentials = await fake_screen_credential_repository.get_active_credentials_by_screen(
        screen.id
    )
    assert active_credentials == []
    assert old_credential.id in fake_screen_credential_repository.credentials


@pytest.mark.asyncio
async def test_reconnect_approval_rejects_screen_owned_by_another_user(
    approve_screen_pairing_session_use_case: ApproveScreenPairingSessionUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    screen = Screen(user_id=uuid4(), name="Other owner's screen")
    fake_screen_repository.screens[screen.id] = screen
    pairing_token = "reconnect-token"
    token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
    session = ScreenPairingSession.create(
        token_hash,
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )
    await fake_screen_pairing_session_repository.save(session)

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
