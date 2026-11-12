"""Backward-compatible exports for repository adapters."""

from adapters.repositories import (
    SqlAlchemyAdminProfileRepository,
    SqlAlchemyAuditLogRepository,
    SqlAlchemyMediaAssetRepository,
    SqlAlchemyPlaylistItemRepository,
    SqlAlchemyPlaylistRepository,
    SqlAlchemyScreenCredentialRepository,
    SqlAlchemyScreenPairingSessionRepository,
    SqlAlchemyScreenPlaylistAssignmentRepository,
    SqlAlchemyScreenRepository,
    SqlAlchemyScreenSyncStateRepository,
)

__all__ = [
    "SqlAlchemyAdminProfileRepository",
    "SqlAlchemyAuditLogRepository",
    "SqlAlchemyMediaAssetRepository",
    "SqlAlchemyPlaylistItemRepository",
    "SqlAlchemyPlaylistRepository",
    "SqlAlchemyScreenCredentialRepository",
    "SqlAlchemyScreenPairingSessionRepository",
    "SqlAlchemyScreenPlaylistAssignmentRepository",
    "SqlAlchemyScreenRepository",
    "SqlAlchemyScreenSyncStateRepository",
]
