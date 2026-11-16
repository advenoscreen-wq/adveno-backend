"""Unit tests for pairing session lifecycle rules."""

from datetime import timedelta
from uuid import uuid4

import pytest

from domain import ScreenPairingSession
from domain.exceptions import DomainError, InvalidStateTransition
from domain.value_object import PairingSessionStatus, PairingType


def test_new_pairing_session_starts_pending_and_unpaired() -> None:
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )

    assert session.status is PairingSessionStatus.PENDING
    assert session.screen_id is None
    assert session.paired_at is None
    assert session.expires_at - session.created_at == timedelta(minutes=10)


def test_pending_new_screen_session_transitions_to_connecting() -> None:
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )

    session.mark_as_connecting()

    assert session.status is PairingSessionStatus.CONNECTING
    assert session.paired_at is None
    assert session.screen_id is None


def test_connecting_new_screen_session_pairs_after_screen_assignment() -> None:
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_connecting()
    session.assign_new_screen(uuid4())
    session.mark_as_paired()

    assert session.status is PairingSessionStatus.PAIRED
    assert session.paired_at is not None
    assert session.screen_id is not None


def test_paired_session_cannot_be_paired_again() -> None:
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_connecting()
    session.assign_new_screen(uuid4())
    session.mark_as_paired()

    with pytest.raises(InvalidStateTransition):
        session.mark_as_paired()


def test_pending_session_cannot_be_assigned_a_new_screen() -> None:
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )

    with pytest.raises(InvalidStateTransition):
        session.assign_new_screen(uuid4())


def test_connecting_new_screen_session_can_be_assigned() -> None:
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_connecting()
    screen_id = uuid4()

    session.assign_new_screen(screen_id)

    assert session.screen_id == screen_id


def test_new_screen_session_cannot_be_assigned_twice() -> None:
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.NEW_SCREEN,
    )
    session.mark_as_connecting()
    session.assign_new_screen(uuid4())

    with pytest.raises(InvalidStateTransition):
        session.assign_new_screen(uuid4())


def test_reconnect_session_requires_screen_when_connecting() -> None:
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )

    with pytest.raises(InvalidStateTransition):
        session.mark_as_connecting()


def test_reconnect_session_pairs_after_screen_credential_step() -> None:
    screen_id = uuid4()
    session = ScreenPairingSession.create(
        "hashed-token",
        timedelta(minutes=10),
        pairing_type=PairingType.RECONNECT_EXISTING,
    )

    session.mark_as_connecting(screen_id=screen_id)
    session.mark_as_paired()

    assert session.status is PairingSessionStatus.PAIRED
    assert session.screen_id == screen_id
    assert session.paired_at is not None


def test_pairing_session_rejects_nonpositive_expiration() -> None:
    with pytest.raises(DomainError):
        ScreenPairingSession.create("hashed-token", timedelta(0))
