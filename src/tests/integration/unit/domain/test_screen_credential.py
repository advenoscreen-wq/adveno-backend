"""Unit tests for screen credential validity and revocation."""

from uuid import uuid4

import pytest

from domain import ScreenCredential
from domain.exceptions import DomainError, InvalidStateTransition


def test_active_credential_is_valid_for_active_screen() -> None:
    credential = ScreenCredential(screen_id=uuid4(), credential_hash="hash-value")

    assert credential.is_valid(screen_active=True)
    assert not credential.is_valid(screen_active=False)


def test_revoking_credential_makes_it_invalid() -> None:
    credential = ScreenCredential(screen_id=uuid4(), credential_hash="hash-value")

    credential.revoke()

    assert credential.revoked_at is not None
    assert not credential.is_valid()


def test_revoked_credential_cannot_be_used() -> None:
    credential = ScreenCredential(screen_id=uuid4(), credential_hash="hash-value")
    credential.revoke()

    with pytest.raises(InvalidStateTransition):
        credential.mark_as_used()


def test_credential_rejects_empty_hash() -> None:
    with pytest.raises(DomainError, match="credential_hash is required"):
        ScreenCredential(screen_id=uuid4(), credential_hash=" ")


def test_active_credential_records_use() -> None:
    credential = ScreenCredential(screen_id=uuid4(), credential_hash="hash-value")

    credential.mark_as_used()

    assert credential.last_used_at is not None
