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
)
from domain.exceptions import (
    DomainError,
    InvalidStateTransition,
    PersistenceConflictError,
    PersistenceError,
)
from domain.value_object import MediaStatus, MediaType, ScreenStatus, SyncStatus

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
    "Playlist",
    "PlaylistItem",
    "Screen",
    "ScreenCredential",
    "ScreenPairingSession",
    "ScreenPlaylistAssignment",
    "ScreenStatus",
    "ScreenSyncState",
    "SyncStatus",
]
