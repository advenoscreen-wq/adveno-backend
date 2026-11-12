from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError, InvalidStateTransition
from domain.value_object import SyncStatus


@dataclass
class ScreenSyncState:
    """Latest synchronization state for a screen."""

    screen_id: UUID
    desired_revision: int = 1
    applied_revision: int = 0
    sync_status: SyncStatus = SyncStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    last_sync_started_at: datetime | None = None
    last_successful_sync_at: datetime | None = None
    last_error: str | None = None
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.desired_revision < 0 or self.applied_revision < 0:
            raise DomainError("sync revisions cannot be negative")
        if self.applied_revision > self.desired_revision:
            raise DomainError("applied revision cannot exceed desired revision")
        for timestamp in (
            self.last_sync_started_at,
            self.last_successful_sync_at,
            self.updated_at,
        ):
            if timestamp is not None:
                validate_timestamp(timestamp)

    def update_desired_revision(self, revision: int) -> None:
        if revision <= self.desired_revision:
            raise DomainError("desired revision must increase")
        self.desired_revision = revision
        self.sync_status = SyncStatus.PENDING
        self.updated_at = utc_now()

    def mark_sync_started(self, *, at: datetime | None = None) -> None:
        if self.sync_status is SyncStatus.SYNCING:
            raise InvalidStateTransition("synchronization is already running")
        started_at = at or utc_now()
        validate_timestamp(started_at)
        self.last_sync_started_at = started_at
        self.sync_status = SyncStatus.SYNCING
        self.last_error = None
        self.updated_at = started_at

    def mark_sync_succeeded(self, applied_revision: int, *, at: datetime | None = None) -> None:
        if applied_revision != self.desired_revision:
            raise DomainError("only the desired revision can be applied")
        completed_at = at or utc_now()
        validate_timestamp(completed_at)
        self.applied_revision = applied_revision
        self.last_successful_sync_at = completed_at
        self.sync_status = SyncStatus.SYNCED
        self.last_error = None
        self.updated_at = completed_at

    def mark_sync_failed(self, error: str, *, at: datetime | None = None) -> None:
        if not error.strip():
            raise DomainError("sync failure reason is required")
        failed_at = at or utc_now()
        validate_timestamp(failed_at)
        self.sync_status = SyncStatus.FAILED
        self.last_error = error
        self.updated_at = failed_at
