from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError, InvalidStateTransition


@dataclass
class ScreenCredential:
    """Hashed credential used by a paired TV device."""

    screen_id: UUID
    credential_hash: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.credential_hash.strip():
            raise DomainError("credential_hash is required")
        for timestamp in (self.created_at, self.last_used_at, self.revoked_at):
            if timestamp is not None:
                validate_timestamp(timestamp)

    def is_valid(
        self,
        *,
        screen_active: bool = True,
        at: datetime | None = None,
    ) -> bool:
        if not screen_active or self.revoked_at is not None:
            return False
        return self.created_at <= (at or utc_now())

    def mark_as_used(self, *, at: datetime | None = None) -> None:
        if self.revoked_at is not None:
            raise InvalidStateTransition("a revoked credential cannot be used")
        used_at = at or utc_now()
        validate_timestamp(used_at)
        self.last_used_at = used_at

    def revoke(self, *, at: datetime | None = None) -> None:
        self.revoked_at = at or utc_now()
