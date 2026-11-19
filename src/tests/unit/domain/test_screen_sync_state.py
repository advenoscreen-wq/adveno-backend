"""Unit tests for screen synchronization transitions."""

from uuid import uuid4

import pytest

from domain import ScreenSyncState
from domain.exceptions import DomainError, InvalidStateTransition
from domain.value_object import SyncStatus


def test_sync_state_moves_from_pending_to_synced_revision() -> None:
    state = ScreenSyncState(screen_id=uuid4(), desired_revision=2)

    state.mark_sync_started()
    state.mark_sync_succeeded(2)

    assert state.applied_revision == 2
    assert state.sync_status is SyncStatus.SYNCED
    assert state.last_successful_sync_at is not None


def test_sync_state_rejects_applying_wrong_revision() -> None:
    state = ScreenSyncState(screen_id=uuid4(), desired_revision=2)
    state.mark_sync_started()

    with pytest.raises(DomainError, match="only the desired revision"):
        state.mark_sync_succeeded(1)

    assert state.sync_status is SyncStatus.SYNCING


def test_sync_state_requires_error_for_failure() -> None:
    state = ScreenSyncState(screen_id=uuid4())

    with pytest.raises(DomainError, match="failure reason is required"):
        state.mark_sync_failed(" ")


def test_sync_state_cannot_start_while_already_syncing() -> None:
    state = ScreenSyncState(screen_id=uuid4())
    state.mark_sync_started()

    with pytest.raises(InvalidStateTransition):
        state.mark_sync_started()


def test_acknowledging_older_desired_revision_keeps_sync_pending() -> None:
    state = ScreenSyncState(screen_id=uuid4(), desired_revision=3, applied_revision=1)

    state.acknowledge_revision(2)

    assert state.applied_revision == 2
    assert state.sync_status is SyncStatus.PENDING
    assert state.last_successful_sync_at is not None


def test_acknowledging_revision_above_desired_is_rejected() -> None:
    state = ScreenSyncState(screen_id=uuid4(), desired_revision=2, applied_revision=1)

    with pytest.raises(DomainError, match="cannot exceed desired revision"):
        state.acknowledge_revision(3)

    assert state.applied_revision == 1
