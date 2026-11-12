from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError, InvalidStateTransition


@dataclass
class ScreenPairingSession:
    """Short-lived, single-use pairing session."""

    screen_id: UUID
    token_hash: str
    expires_at: datetime
    id: UUID = field(default_factory=uuid4)
    paired_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.token_hash.strip():
            raise DomainError("token_hash is required")
        validate_timestamp(self.expires_at)
        validate_timestamp(self.created_at)
        if self.paired_at is not None:
            validate_timestamp(self.paired_at)

    @classmethod
    def create(cls, screen_id: UUID, token_hash: str, ttl: timedelta) -> ScreenPairingSession:
        if ttl <= timedelta(0):
            raise DomainError("pairing session TTL must be positive")
        created_at = utc_now()
        return cls(
            screen_id=screen_id,
            token_hash=token_hash,
            expires_at=created_at + ttl,
            created_at=created_at,
        )

    def is_expired(self, *, at: datetime | None = None) -> bool:
        check_at = at or utc_now()
        validate_timestamp(check_at)
        return check_at >= self.expires_at

    def is_valid(self, *, at: datetime | None = None) -> bool:
        return self.paired_at is None and not self.is_expired(at=at)

    def mark_as_paired(self, *, at: datetime | None = None) -> None:
        if not self.is_valid(at=at):
            raise InvalidStateTransition("pairing session is expired or already paired")
        self.paired_at = at or utc_now()
