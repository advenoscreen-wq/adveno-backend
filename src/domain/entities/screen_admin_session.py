"""Short-lived PIN-activated administrative access for one screen."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError


@dataclass
class ScreenAdminSession:
    screen_id: UUID
    code_hash: str
    expires_at: datetime
    last_activity_at: datetime = field(default_factory=utc_now)
    token_hash: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.code_hash.strip():
            raise DomainError("admin PIN hash is required")
        for timestamp in (self.expires_at, self.last_activity_at, self.created_at, self.revoked_at):
            if timestamp is not None:
                validate_timestamp(timestamp)

    def can_verify_pin(self, *, at: datetime | None = None) -> bool:
        now = at or utc_now()
        validate_timestamp(now)
        return self.token_hash is None and self.revoked_at is None and now < self.expires_at

    def is_active(self, *, idle_timeout: timedelta, at: datetime | None = None) -> bool:
        now = at or utc_now()
        validate_timestamp(now)
        return (
            self.token_hash is not None
            and self.revoked_at is None
            and now < self.expires_at
            and now - self.last_activity_at < idle_timeout
        )

    def activate(
        self,
        token_hash: str,
        *,
        absolute_ttl: timedelta,
        at: datetime | None = None,
    ) -> None:
        now = at or utc_now()
        validate_timestamp(now)
        if not self.can_verify_pin(at=now):
            raise DomainError("admin PIN session is unavailable")
        if not token_hash.strip() or absolute_ttl <= timedelta(0):
            raise DomainError("valid session token and lifetime are required")
        self.token_hash = token_hash
        self.last_activity_at = now
        self.expires_at = now + absolute_ttl

    def record_activity(self, *, at: datetime | None = None) -> None:
        now = at or utc_now()
        validate_timestamp(now)
        self.last_activity_at = now

    def revoke(self, *, at: datetime | None = None) -> None:
        revoked_at = at or utc_now()
        validate_timestamp(revoked_at)
        if self.revoked_at is None:
            self.revoked_at = revoked_at


__all__ = ["ScreenAdminSession"]
