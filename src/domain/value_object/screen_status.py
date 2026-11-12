from enum import StrEnum


class ScreenStatus(StrEnum):
    """Administrative activation state for a screen."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
