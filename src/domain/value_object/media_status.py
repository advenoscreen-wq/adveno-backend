from enum import StrEnum


class MediaStatus(StrEnum):
    """Lifecycle state of a media asset."""

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
