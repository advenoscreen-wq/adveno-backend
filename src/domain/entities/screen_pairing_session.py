from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError, InvalidStateTransition
from domain.value_object import PairingSessionStatus, PairingType


@dataclass
class ScreenPairingSession:
    """Short-lived, single-use pairing session."""

    token_hash: str
    expires_at: datetime
    pairing_type: PairingType | None = None
    screen_id: UUID | None = None
    status: PairingSessionStatus = PairingSessionStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    paired_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        try:
            if self.pairing_type is not None:
                self.pairing_type = PairingType(self.pairing_type)
            self.status = PairingSessionStatus(self.status)
        except (TypeError, ValueError) as error:
            raise DomainError("pairing type or status is invalid") from error
        if not self.token_hash.strip():
            raise DomainError("token_hash is required")
        if (self.status is PairingSessionStatus.PAIRED) != (self.paired_at is not None):
            raise DomainError("paired status and paired_at must be set together")
        if self.pairing_type is None:
            if self.screen_id is not None or self.status is PairingSessionStatus.PAIRED:
                raise DomainError("unselected pairing sessions cannot reference a screen")
        elif self.pairing_type is PairingType.RECONNECT_EXISTING:
            if self.paired_at is not None and self.screen_id is None:
                raise DomainError("paired reconnect sessions require a screen_id")
        elif self.pairing_type is PairingType.NEW_SCREEN and (
            (self.paired_at is None) != (self.screen_id is None)
        ):
            raise DomainError("NEW_SCREEN pairing requires a screen_id only after pairing")
        validate_timestamp(self.expires_at)
        validate_timestamp(self.created_at)
        if self.paired_at is not None:
            validate_timestamp(self.paired_at)

    @classmethod
    def create(
        cls,
        token_hash: str,
        ttl: timedelta,
        *,
        pairing_type: PairingType | None = None,
        screen_id: UUID | None = None,
    ) -> ScreenPairingSession:
        if ttl <= timedelta(0):
            raise DomainError("pairing session TTL must be positive")
        created_at = utc_now()
        return cls(
            token_hash=token_hash,
            expires_at=created_at + ttl,
            pairing_type=pairing_type,
            screen_id=screen_id,
            created_at=created_at,
        )

    def is_expired(self, *, at: datetime | None = None) -> bool:
        check_at = at or utc_now()
        validate_timestamp(check_at)
        return check_at >= self.expires_at

    def is_valid(self, *, at: datetime | None = None) -> bool:
        return (
            self.status is PairingSessionStatus.PENDING
            and self.paired_at is None
            and not self.is_expired(at=at)
        )

    def mark_as_paired(
        self,
        *,
        screen_id: UUID | None = None,
        at: datetime | None = None,
    ) -> None:
        if not self.is_valid(at=at):
            raise InvalidStateTransition("pairing session is expired or already paired")
        if self.pairing_type is None:
            raise InvalidStateTransition("pairing type must be selected before approval")
        if self.pairing_type is PairingType.NEW_SCREEN:
            if screen_id is None:
                raise InvalidStateTransition(
                    "new screen must be registered before pairing completes"
                )
            self.screen_id = screen_id
        elif self.pairing_type is PairingType.RECONNECT_EXISTING:
            if self.screen_id is None:
                if screen_id is None:
                    raise InvalidStateTransition("reconnect pairing requires a selected screen")
                self.screen_id = screen_id
            elif screen_id is not None and screen_id != self.screen_id:
                raise InvalidStateTransition("reconnect pairing cannot change the selected screen")
        self.paired_at = at or utc_now()
        self.status = PairingSessionStatus.PAIRED
