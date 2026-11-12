from enum import StrEnum


class SyncStatus(StrEnum):
    """Screen synchronization lifecycle state."""

    PENDING = "PENDING"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"
