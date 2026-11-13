"""Results returned by screen pairing use cases."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.value_object import PairingSessionStatus, PairingType


@dataclass(frozen=True)
class CreateScreenPairingSessionResult:
    session_id: UUID
    pairing_token: str
    expires_at: datetime


@dataclass(frozen=True)
class GetScreenPairingSessionStatusResult:
    status: PairingSessionStatus


@dataclass(frozen=True)
class VerifyScreenPairingSessionResult:
    session_id: UUID
    status: PairingSessionStatus
    pairing_type: PairingType | None
    screen_id: UUID | None
    screen_exists: bool
    expires_at: datetime
    created_at: datetime
