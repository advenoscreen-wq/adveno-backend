"""Explicit mappings between SQLAlchemy and domain entities."""

from domain.entities.entities import (
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
from domain.value_object.enums import MediaStatus, MediaType, ScreenStatus, SyncStatus
from drivers.database.models.entities import (
    AdminProfileModel,
    AuditLogModel,
    MediaAssetModel,
    PlaylistItemModel,
    PlaylistModel,
    ScreenCredentialModel,
    ScreenModel,
    ScreenPairingSessionModel,
    ScreenPlaylistAssignmentModel,
    ScreenSyncStateModel,
)


def to_admin_profile(model: AdminProfileModel) -> AdminProfile:
    return AdminProfile(
        id=model.id,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_screen(model: ScreenModel) -> Screen:
    return Screen(
        id=model.id,
        screen_code=model.screen_code,
        name=model.name,
        device_model=model.device_model,
        app_version=model.app_version,
        status=ScreenStatus(model.status),
        last_seen_at=model.last_seen_at,
        last_successful_sync_at=model.last_successful_sync_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_pairing_session(model: ScreenPairingSessionModel) -> ScreenPairingSession:
    return ScreenPairingSession(
        id=model.id,
        screen_id=model.screen_id,
        token_hash=model.token_hash,
        expires_at=model.expires_at,
        paired_at=model.paired_at,
        created_at=model.created_at,
    )


def to_credential(model: ScreenCredentialModel) -> ScreenCredential:
    return ScreenCredential(
        id=model.id,
        screen_id=model.screen_id,
        credential_hash=model.credential_hash,
        created_at=model.created_at,
        last_used_at=model.last_used_at,
        revoked_at=model.revoked_at,
    )


def to_media_asset(model: MediaAssetModel) -> MediaAsset:
    return MediaAsset(
        id=model.id,
        name=model.name,
        media_type=MediaType(model.media_type),
        mime_type=model.mime_type,
        storage_path=model.storage_path,
        file_size=model.file_size,
        checksum=model.checksum,
        width=model.width,
        height=model.height,
        duration_seconds=model.duration_seconds,
        status=MediaStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_playlist_item(model: PlaylistItemModel) -> PlaylistItem:
    return PlaylistItem(
        id=model.id,
        playlist_id=model.playlist_id,
        media_asset_id=model.media_asset_id,
        position=model.position,
        duration_seconds=model.duration_seconds,
        created_at=model.created_at,
    )


def to_playlist(model: PlaylistModel, items: list[PlaylistItem] | None = None) -> Playlist:
    return Playlist(
        id=model.id,
        name=model.name,
        description=model.description,
        version=model.version,
        items=items or [],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_assignment(model: ScreenPlaylistAssignmentModel) -> ScreenPlaylistAssignment:
    return ScreenPlaylistAssignment(
        id=model.id,
        screen_id=model.screen_id,
        playlist_id=model.playlist_id,
        assigned_at=model.assigned_at,
        unassigned_at=model.unassigned_at,
    )


def to_sync_state(model: ScreenSyncStateModel) -> ScreenSyncState:
    return ScreenSyncState(
        id=model.screen_id,
        screen_id=model.screen_id,
        desired_revision=model.desired_revision,
        applied_revision=model.applied_revision,
        sync_status=SyncStatus(model.sync_status),
        last_sync_started_at=model.last_sync_started_at,
        last_successful_sync_at=model.last_successful_sync_at,
        last_error=model.last_error,
        updated_at=model.updated_at,
    )


def to_audit_log(model: AuditLogModel) -> AuditLog:
    return AuditLog(
        id=model.id,
        admin_id=model.admin_id,
        screen_id=model.screen_id,
        action=model.action,
        details=dict(model.details),
        created_at=model.created_at,
    )


def apply_admin_profile(entity: AdminProfile, model: AdminProfileModel) -> None:
    model.id = entity.id
    model.is_active = entity.is_active
    model.updated_at = entity.updated_at


def apply_screen(entity: Screen, model: ScreenModel) -> None:
    model.id = entity.id
    model.screen_code = entity.screen_code
    model.name = entity.name
    model.device_model = entity.device_model
    model.app_version = entity.app_version
    model.status = entity.status.value
    model.last_seen_at = entity.last_seen_at
    model.last_successful_sync_at = entity.last_successful_sync_at
    model.updated_at = entity.updated_at


def apply_pairing_session(entity: ScreenPairingSession, model: ScreenPairingSessionModel) -> None:
    model.id = entity.id
    model.screen_id = entity.screen_id
    model.token_hash = entity.token_hash
    model.expires_at = entity.expires_at
    model.paired_at = entity.paired_at


def apply_credential(entity: ScreenCredential, model: ScreenCredentialModel) -> None:
    model.id = entity.id
    model.screen_id = entity.screen_id
    model.credential_hash = entity.credential_hash
    model.last_used_at = entity.last_used_at
    model.revoked_at = entity.revoked_at


def apply_media_asset(entity: MediaAsset, model: MediaAssetModel) -> None:
    model.id = entity.id
    model.name = entity.name
    model.media_type = entity.media_type.value
    model.mime_type = entity.mime_type
    model.storage_path = entity.storage_path
    model.file_size = entity.file_size
    model.checksum = entity.checksum
    model.width = entity.width
    model.height = entity.height
    model.duration_seconds = entity.duration_seconds
    model.status = entity.status.value
    model.updated_at = entity.updated_at


def apply_playlist(entity: Playlist, model: PlaylistModel) -> None:
    model.id = entity.id
    model.name = entity.name
    model.description = entity.description
    model.version = entity.version
    model.updated_at = entity.updated_at


def apply_playlist_item(entity: PlaylistItem, model: PlaylistItemModel) -> None:
    model.id = entity.id
    model.playlist_id = entity.playlist_id
    model.media_asset_id = entity.media_asset_id
    model.position = entity.position
    model.duration_seconds = entity.duration_seconds


def apply_assignment(
    entity: ScreenPlaylistAssignment, model: ScreenPlaylistAssignmentModel
) -> None:
    model.id = entity.id
    model.screen_id = entity.screen_id
    model.playlist_id = entity.playlist_id
    model.assigned_at = entity.assigned_at
    model.unassigned_at = entity.unassigned_at


def apply_sync_state(entity: ScreenSyncState, model: ScreenSyncStateModel) -> None:
    model.screen_id = entity.screen_id
    model.desired_revision = entity.desired_revision
    model.applied_revision = entity.applied_revision
    model.sync_status = entity.sync_status.value
    model.last_sync_started_at = entity.last_sync_started_at
    model.last_successful_sync_at = entity.last_successful_sync_at
    model.last_error = entity.last_error
    model.updated_at = entity.updated_at
