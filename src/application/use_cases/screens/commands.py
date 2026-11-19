"""Commands accepted by screen use cases."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AcknowledgeScreenSyncCommand:
    applied_revision: int
