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
