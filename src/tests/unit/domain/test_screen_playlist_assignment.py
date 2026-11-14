"""Unit tests for playlist assignment history."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from domain import ScreenPlaylistAssignment
from domain.exceptions import InvalidStateTransition


def test_assignment_is_active_until_unassigned() -> None:
    assignment = ScreenPlaylistAssignment(screen_id=uuid4(), playlist_id=uuid4())

    assert assignment.is_active()

    assignment.unassign()

    assert not assignment.is_active()
    assert assignment.unassigned_at is not None


def test_inactive_assignment_cannot_be_unassigned_again() -> None:
    assignment = ScreenPlaylistAssignment(screen_id=uuid4(), playlist_id=uuid4())
    assignment.unassign(at=datetime.now(UTC))

    with pytest.raises(InvalidStateTransition):
        assignment.unassign()
