"""Unit tests for screen state and identity behavior."""

import re
from uuid import uuid4

import pytest

from domain import Screen
from domain.exceptions import InvalidStateTransition
from domain.value_object import ScreenStatus


def test_screen_generates_unique_human_readable_code() -> None:
    first = Screen(user_id=uuid4(), name="First TV")
    second = Screen(user_id=uuid4(), name="Second TV")
    pattern = r"SCR-(?:[A-HJ-NP-Z2-9]{4}-){3}[A-HJ-NP-Z2-9]{4}"

    assert re.fullmatch(pattern, first.screen_code)
    assert re.fullmatch(pattern, second.screen_code)
    assert first.screen_code != second.screen_code


def test_screen_heartbeat_updates_device_information() -> None:
    screen = Screen(user_id=uuid4(), name="Lobby")

    screen.record_heartbeat(device_model="Model X", app_version="2.1.0")

    assert screen.last_seen_at is not None
    assert screen.device_model == "Model X"
    assert screen.app_version == "2.1.0"


def test_inactive_screen_cannot_record_heartbeat() -> None:
    screen = Screen(user_id=uuid4(), name="Lobby")
    screen.deactivate()

    with pytest.raises(InvalidStateTransition):
        screen.record_heartbeat()

    assert screen.status is ScreenStatus.INACTIVE
    assert screen.last_seen_at is None


def test_screen_can_be_reactivated() -> None:
    screen = Screen(user_id=uuid4(), name="Lobby")
    screen.deactivate()

    screen.activate()

    assert screen.status is ScreenStatus.ACTIVE
