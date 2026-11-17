"""Commands for screen pairing use cases."""

from dataclasses import dataclass
from uuid import UUID

from domain.value_object import PairingType


@dataclass(frozen=True)
class CreateScreenPairingSessionCommand:
    pairing_type: PairingType


@dataclass(frozen=True)
class GetScreenPairingSessionStatusCommand:
    session_id: UUID
    pairing_token: str


@dataclass(frozen=True)
class VerifyScreenPairingSessionCommand:
    pairing_token: str


@dataclass(frozen=True)
class ApproveScreenPairingSessionCommand:
    pairing_token: str
    user_id: UUID
    screen_id: UUID | None = None


@dataclass(frozen=True)
class CreatePairedScreenCommand:
    session_id: UUID
    pairing_token: str
    user_id: UUID
    name: str
    device_model: str | None = None
    app_version: str | None = None


@dataclass(frozen=True)
class IssuePairedScreenCredentialCommand:
    session_id: UUID
    pairing_token: str
