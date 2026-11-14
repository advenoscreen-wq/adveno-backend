"""Unit tests for completion checks and paired credential delivery."""

import hashlib
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest

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
async def test_completion_requires_paired_session_screen_and_active_credential(
    check_pairing_completion_use_case: CheckPairingCompletionUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    pairing_token = "completion-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_paired()
    await fake_screen_pairing_session_repository.save(session)

    result = await check_pairing_completion_use_case(
        CheckPairingCompletionCommand(pairing_token=pairing_token)
    )
    assert result.status is PairingSessionStatus.PAIRED
    assert result.screen_id is None
    assert result.paired_at is not None
    assert not result.completed

    screen_id = uuid4()
    session.assign_new_screen(screen_id)
    await fake_screen_credential_repository.save(
        ScreenCredential(screen_id=screen_id, credential_hash="active-hash")
    )
    result = await check_pairing_completion_use_case(
        CheckPairingCompletionCommand(pairing_token=pairing_token)
    )
    assert result.completed
    assert result.screen_id == screen_id

    credential = await fake_screen_credential_repository.get_active_credential_by_screen(
        screen_id
    )
    assert credential is not None
    credential.revoke()
    await fake_screen_credential_repository.update(credential)
    result = await check_pairing_completion_use_case(
        CheckPairingCompletionCommand(pairing_token=pairing_token)
    )
    assert not result.completed


@pytest.mark.asyncio
async def test_credential_endpoint_replaces_active_credential_and_returns_raw_secret(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    pairing_token = "credential-pairing-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
        screen_id=uuid4(),
    )
    session.mark_as_paired(screen_id=session.screen_id)
    await fake_screen_pairing_session_repository.save(session)
    old_credential = ScreenCredential(
        screen_id=session.screen_id,
        credential_hash="old-credential-hash",
    )
    fake_screen_credential_repository.credentials[old_credential.id] = old_credential

    result = await issue_paired_screen_credential_use_case(
        IssuePairedScreenCredentialCommand(
            session_id=session.id,
            pairing_token=pairing_token,
        )
    )

    assert result.screen_id == session.screen_id
    assert old_credential.revoked_at is not None
    active = await fake_screen_credential_repository.get_active_credentials_by_screen(
        session.screen_id
    )
    assert len(active) == 1
    assert active[0].credential_hash == hashlib.sha256(
        result.credential.encode("utf-8")
    ).hexdigest()
    assert result.credential != active[0].credential_hash


@pytest.mark.asyncio
async def test_credential_endpoint_creates_first_credential_after_reconnect_approval(
    issue_paired_screen_credential_use_case: IssuePairedScreenCredentialUseCase,
    fake_screen_pairing_session_repository: Any,
    fake_screen_credential_repository: Any,
) -> None:
    pairing_token = "missing-credential-token"
    session = ScreenPairingSession.create(
        hashlib.sha256(pairing_token.encode()).hexdigest(),
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
        screen_id=uuid4(),
    )
    session.mark_as_paired(screen_id=session.screen_id)
    await fake_screen_pairing_session_repository.save(session)

    result = await issue_paired_screen_credential_use_case(
        IssuePairedScreenCredentialCommand(
            session_id=session.id,
            pairing_token=pairing_token,
        )
    )
    active = await fake_screen_credential_repository.get_active_credentials_by_screen(
        session.screen_id
    )
    assert len(active) == 1
    assert active[0].credential_hash == hashlib.sha256(
        result.credential.encode("utf-8")
    ).hexdigest()
