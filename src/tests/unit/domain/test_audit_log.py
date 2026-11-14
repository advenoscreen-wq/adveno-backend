"""Unit tests for audit log invariants."""

from uuid import uuid4

import pytest

from domain import AuditLog
from domain.exceptions import DomainError


def test_audit_log_copies_details_on_creation() -> None:
    details = {"source": "pairing"}
    entry = AuditLog(action="SCREEN_PAIRED", details=details)

    details["source"] = "changed"

    assert entry.details == {"source": "pairing"}


def test_audit_log_rejects_blank_action() -> None:
    with pytest.raises(DomainError, match="audit action is required"):
        AuditLog(action=" ")


def test_audit_log_accepts_optional_screen_reference() -> None:
    screen_id = uuid4()
    entry = AuditLog(action="SCREEN_UPDATED", screen_id=screen_id)

    assert entry.screen_id == screen_id
