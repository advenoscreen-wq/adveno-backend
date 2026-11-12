from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError


@dataclass(frozen=True)
class AuditLog:
    """Append-only audit event."""

    action: str
    admin_id: UUID | None = None
    screen_id: UUID | None = None
    details: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.action.strip():
            raise DomainError("audit action is required")
        validate_timestamp(self.created_at)
        object.__setattr__(self, "details", dict(self.details))
