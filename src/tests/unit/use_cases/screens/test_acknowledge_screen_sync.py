"""Unit tests for screen synchronization acknowledgments."""

import hashlib
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.exceptions.screen import SyncRevisionConflictError
from application.use_cases.screens.acknowledge_screen_sync_use_case import (
    AcknowledgeScreenSyncUseCase,
)
from application.use_cases.screens.commands import AcknowledgeScreenSyncCommand
from domain import Screen, ScreenCredential, ScreenSyncState
from domain.value_object import SyncStatus


@pytest.mark.asyncio
async def test_acknowledgment_marks_desired_revision_as_synced(
    acknowledge_screen_sync_use_case: AcknowledgeScreenSyncUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_sync_state_repo: Mock,
) -> None:
    raw_credential = "screen-sync-secret"
    screen = Screen(user_id=uuid4(), name="Sync TV")
    credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
    )
    state = ScreenSyncState(screen_id=screen.id, desired_revision=5, applied_revision=4)
    screen_repo.get_by_id.return_value = screen
    screen_credential_repo.get_by_hash.return_value = credential
    screen_sync_state_repo.get_by_screen_id.return_value = state

    await acknowledge_screen_sync_use_case(
        credential=raw_credential,
        command=AcknowledgeScreenSyncCommand(applied_revision=5),
    )

    assert state.applied_revision == 5
    assert state.sync_status is SyncStatus.SYNCED
    assert state.last_successful_sync_at is not None
    assert screen.last_successful_sync_at is not None
    screen_sync_state_repo.update.assert_awaited_once_with(state)


@pytest.mark.asyncio
async def test_acknowledgment_rejects_revision_above_desired(
    acknowledge_screen_sync_use_case: AcknowledgeScreenSyncUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_sync_state_repo: Mock,
) -> None:
    raw_credential = "screen-sync-secret"
    screen = Screen(user_id=uuid4(), name="Sync TV")
    credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
    )
    state = ScreenSyncState(screen_id=screen.id, desired_revision=4, applied_revision=2)
    screen_repo.get_by_id.return_value = screen
    screen_credential_repo.get_by_hash.return_value = credential
    screen_sync_state_repo.get_by_screen_id.return_value = state

    with pytest.raises(SyncRevisionConflictError):
        await acknowledge_screen_sync_use_case(
            credential=raw_credential,
            command=AcknowledgeScreenSyncCommand(applied_revision=5),
        )

    assert state.applied_revision == 2
    screen_sync_state_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_stale_acknowledgment_does_not_move_revision_backwards(
    acknowledge_screen_sync_use_case: AcknowledgeScreenSyncUseCase,
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_sync_state_repo: Mock,
) -> None:
    raw_credential = "screen-sync-secret"
    screen = Screen(user_id=uuid4(), name="Sync TV")
    credential = ScreenCredential(
        screen_id=screen.id,
        credential_hash=hashlib.sha256(raw_credential.encode()).hexdigest(),
    )
    state = ScreenSyncState(screen_id=screen.id, desired_revision=5, applied_revision=4)
    screen_repo.get_by_id.return_value = screen
    screen_credential_repo.get_by_hash.return_value = credential
    screen_sync_state_repo.get_by_screen_id.return_value = state

    await acknowledge_screen_sync_use_case(
        credential=raw_credential,
        command=AcknowledgeScreenSyncCommand(applied_revision=3),
    )

    assert state.applied_revision == 4
    screen_sync_state_repo.update.assert_not_awaited()
