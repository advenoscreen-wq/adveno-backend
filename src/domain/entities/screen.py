from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError, InvalidStateTransition
from domain.value_object import ScreenStatus


@dataclass
class Screen:
    """Registered Adveno TV screen."""

    user_id: UUID
    id: UUID = field(default_factory=uuid4)
    screen_code: str = field(default_factory=lambda: uuid4().hex.upper())
    name: str = ""
    device_model: str | None = None
    app_version: str | None = None
    status: ScreenStatus = ScreenStatus.ACTIVE
    last_seen_at: datetime | None = None
    last_successful_sync_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.screen_code.strip():
            raise DomainError("screen_code is required")
        if not self.name.strip():
            raise DomainError("screen name is required")
        for timestamp in (
            self.last_seen_at,
            self.last_successful_sync_at,
            self.created_at,
            self.updated_at,
        ):
            if timestamp is not None:
                validate_timestamp(timestamp)

    @property
    def is_active(self) -> bool:
        """Return whether the screen is administratively active."""
        return self.status is ScreenStatus.ACTIVE

    def activate(self) -> None:
        self.status = ScreenStatus.ACTIVE
        self.updated_at = utc_now()

    def deactivate(self) -> None:
        self.status = ScreenStatus.INACTIVE
        self.updated_at = utc_now()

    def record_heartbeat(
        self,
        *,
        at: datetime | None = None,
        device_model: str | None = None,
        app_version: str | None = None,
    ) -> None:
        if not self.is_active:
            raise InvalidStateTransition("an inactive screen cannot record a heartbeat")
        heartbeat_at = at or utc_now()
        validate_timestamp(heartbeat_at)
        self.last_seen_at = heartbeat_at
        self.update_device_info(device_model=device_model, app_version=app_version)

    def record_successful_sync(self, *, at: datetime | None = None) -> None:
        if not self.is_active:
            raise InvalidStateTransition("an inactive screen cannot complete synchronization")
        sync_at = at or utc_now()
        validate_timestamp(sync_at)
        self.last_successful_sync_at = sync_at
        self.updated_at = sync_at

    def update_device_info(
        self,
        *,
        device_model: str | None = None,
        app_version: str | None = None,
    ) -> None:
        if device_model is not None:
            self.device_model = device_model
        if app_version is not None:
            self.app_version = app_version
        self.updated_at = utc_now()
