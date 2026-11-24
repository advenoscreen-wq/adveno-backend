"""Unit tests for protected screen administration session rules."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from domain import ScreenAdminSession


def _active_session() -> ScreenAdminSession:
    now = datetime.now(UTC)
    return ScreenAdminSession(
        screen_id=uuid4(),
        code_hash="scrypt$pin-hash",
        token_hash="hashed-session-token",
        created_at=now - timedelta(minutes=1),
        last_activity_at=now,
        expires_at=now + timedelta(minutes=15),
    )


def test_admin_session_is_active_before_absolute_and_idle_expiration() -> None:
    now = datetime.now(UTC)
    session = _active_session()

    assert session.is_active(idle_timeout=timedelta(minutes=5), at=now)


def test_admin_session_expires_after_idle_timeout() -> None:
    now = datetime.now(UTC)
    session = _active_session()
    session.last_activity_at = now - timedelta(minutes=6)

    assert not session.is_active(idle_timeout=timedelta(minutes=5), at=now)


def test_admin_session_expires_at_absolute_deadline() -> None:
    now = datetime.now(UTC)
    session = _active_session()
    session.expires_at = now

    assert not session.is_active(idle_timeout=timedelta(minutes=5), at=now)


def test_revoked_admin_session_is_inactive() -> None:
    now = datetime.now(UTC)
    session = _active_session()
    session.revoke(at=now)

    assert not session.is_active(idle_timeout=timedelta(minutes=5), at=now)


def test_pin_challenge_cannot_be_reused_after_activation() -> None:
    now = datetime.now(UTC)
    session = ScreenAdminSession(
        screen_id=uuid4(),
        code_hash="scrypt$pin-hash",
        created_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    session.activate(
        "hashed-session-token",
        absolute_ttl=timedelta(minutes=15),
        at=now,
    )

    assert not session.can_verify_pin(at=now)
