"""Public domain API."""

from domain.entities import (
    AdminProfile,
    AuditLog,
    MediaAsset,
    Playlist,
    PlaylistItem,
    Screen,
    ScreenAdminSession,
    ScreenCredential,
    ScreenPairingSession,
    ScreenPlaybackEvent,
    ScreenPlaylistAssignment,
    ScreenSyncState,
    User,
)
from domain.exceptions import (
    DomainError,
    InvalidStateTransition,
    PersistenceConflictError,
    PersistenceError,
)
from domain.value_object import (
    MediaStatus,
    MediaType,
    PairingSessionStatus,
    PairingType,
    ScreenStatus,
    SyncStatus,
    UserRole,
)

__all__ = [
    "AdminProfile",
    "AuditLog",
    "DomainError",
    "InvalidStateTransition",
    "MediaAsset",
    "MediaStatus",
    "MediaType",
    "PersistenceConflictError",
    "PersistenceError",
    "PairingType",
    "PairingSessionStatus",
    "Playlist",
    "PlaylistItem",
    "Screen",
    "ScreenAdminSession",
    "ScreenCredential",
    "ScreenPairingSession",
    "ScreenPlaybackEvent",
    "ScreenPlaylistAssignment",
    "ScreenStatus",
    "ScreenSyncState",
    "SyncStatus",
    "User",
    "UserRole",
]
