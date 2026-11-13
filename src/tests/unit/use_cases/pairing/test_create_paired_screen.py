"""Unit tests for screen creation from a paired session."""

import hashlib
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest

from application.exceptions.pairing import (
    PairingScreenAlreadyCreatedError,
    PairingSessionNotFoundError,
    PairingSessionNotPairedError,
)
from application.use_cases.pairing.commands import CreatePairedScreenCommand
from application.use_cases.pairing.create_paired_screen_use_case import (
    CreatePairedScreenUseCase,
)
from domain import ScreenPairingSession
from domain.value_object import PairingType


@pytest.mark.asyncio
async def test_creates_screen_and_assigns_it_to_paired_new_screen_session(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    pairing_token = "tv-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_paired()
    await fake_screen_pairing_session_repository.save(session)
    user_id = uuid4()

    result = await create_paired_screen_use_case(
        CreatePairedScreenCommand(
            session_id=session.id,
            pairing_token=pairing_token,
            user_id=user_id,
            name="Lobby TV",
            device_model="Model X",
            app_version="1.2.3",
        )
    )

    screen = fake_screen_repository.screens[result.screen_id]
    assert screen.user_id == user_id
    assert screen.name == "Lobby TV"
    assert screen.device_model == "Model X"
    assert screen.app_version == "1.2.3"
    assert result.screen_code == screen.screen_code
    assert session.screen_id == screen.id
    credentials = await fake_screen_credential_repository.get_active_credentials_by_screen(
        screen.id
    )
    assert len(credentials) == 1
    assert credentials[0].credential_hash == hashlib.sha256(
        result.credential.encode("utf-8")
    ).hexdigest()
    assert result.credential != credentials[0].credential_hash

    with pytest.raises(PairingScreenAlreadyCreatedError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(
                session_id=session.id,
                pairing_token=pairing_token,
                user_id=user_id,
                name="Duplicate TV",
            )
        )
    assert len(fake_screen_repository.screens) == 1


@pytest.mark.asyncio
async def test_does_not_create_screen_before_session_is_paired(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    pairing_token = "pending-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    await fake_screen_pairing_session_repository.save(session)

    with pytest.raises(PairingSessionNotPairedError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(
                session_id=session.id,
                pairing_token=pairing_token,
                user_id=uuid4(),
                name="Lobby TV",
            )
        )

    assert fake_screen_repository.screens == {}
    assert fake_screen_credential_repository.credentials == {}


@pytest.mark.asyncio
async def test_rejects_session_id_and_pairing_token_that_do_not_match(
    create_paired_screen_use_case: CreatePairedScreenUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    valid_token = "valid-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(valid_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_paired()
    await fake_screen_pairing_session_repository.save(session)

    with pytest.raises(PairingSessionNotFoundError):
        await create_paired_screen_use_case(
            CreatePairedScreenCommand(
                session_id=session.id,
                pairing_token="different-token",
                user_id=uuid4(),
                name="Lobby TV",
            )
        )

    assert fake_screen_repository.screens == {}
    assert fake_screen_credential_repository.credentials == {}
