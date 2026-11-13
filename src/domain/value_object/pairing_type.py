from enum import StrEnum


class PairingType(StrEnum):
    """Supported screen pairing flows."""

    NEW_SCREEN = "NEW_SCREEN"
    RECONNECT_EXISTING = "RECONNECT_EXISTING"
