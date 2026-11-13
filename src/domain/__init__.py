"""Public domain API."""

from domain.entities import (
    AdminProfile,
    AuditLog,
    MediaAsset,
    Playlist,
    PlaylistItem,
    Screen,
    ScreenCredential,
    ScreenPairingSession,
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
    "Playlist",
    "PlaylistItem",
    "Screen",
    "ScreenCredential",
    "ScreenPairingSession",
    "ScreenPlaylistAssignment",
    "ScreenStatus",
    "ScreenSyncState",
    "SyncStatus",
    "User",
    "UserRole",
]
