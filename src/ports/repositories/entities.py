"""Backward-compatible exports for repository ports."""

from ports.repositories import (
    AdminProfileRepository,
    AuditLogRepository,
    MediaAssetRepository,
    PlaylistItemRepository,
    PlaylistRepository,
    ScreenCredentialRepository,
    ScreenPairingSessionRepository,
    ScreenPlaylistAssignmentRepository,
    ScreenRepository,
    ScreenSyncStateRepository,
)

__all__ = [
    "AdminProfileRepository",
    "AuditLogRepository",
    "MediaAssetRepository",
    "PlaylistItemRepository",
    "PlaylistRepository",
    "ScreenCredentialRepository",
    "ScreenPairingSessionRepository",
    "ScreenPlaylistAssignmentRepository",
    "ScreenRepository",
    "ScreenSyncStateRepository",
]
