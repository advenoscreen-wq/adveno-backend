from enum import StrEnum


class PairingSessionStatus(StrEnum):
    """Lifecycle state for a screen pairing session."""

    PENDING = "PENDING"
    CONNECTING = "CONNECTING"
    PAIRED = "PAIRED"
    EXPIRED = "EXPIRED"
