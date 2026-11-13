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
    SqlAlchemyUserRepository,
)

__all__ = [
    "SqlAlchemyAdminProfileRepository",
    "SqlAlchemyUserRepository",
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
