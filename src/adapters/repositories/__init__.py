"""Repository adapters."""

from adapters.repositories.admin_profile_repository import SqlAlchemyAdminProfileRepository
from adapters.repositories.audit_log_repository import SqlAlchemyAuditLogRepository
from adapters.repositories.media_asset_repository import SqlAlchemyMediaAssetRepository
from adapters.repositories.playlist_item_repository import SqlAlchemyPlaylistItemRepository
from adapters.repositories.playlist_repository import SqlAlchemyPlaylistRepository
from adapters.repositories.screen_credential_repository import SqlAlchemyScreenCredentialRepository
from adapters.repositories.screen_pairing_session_repository import (
    SqlAlchemyScreenPairingSessionRepository,
)
from adapters.repositories.screen_playlist_assignment_repository import (
    SqlAlchemyScreenPlaylistAssignmentRepository,
)
from adapters.repositories.screen_repository import SqlAlchemyScreenRepository
from adapters.repositories.screen_sync_state_repository import SqlAlchemyScreenSyncStateRepository
from adapters.repositories.user_repository import SqlAlchemyUserRepository

__all__ = [
    "SqlAlchemyAdminProfileRepository",
    "SqlAlchemyUserRepository",
    "SqlAlchemyScreenRepository",
    "SqlAlchemyScreenPairingSessionRepository",
    "SqlAlchemyScreenCredentialRepository",
    "SqlAlchemyMediaAssetRepository",
    "SqlAlchemyPlaylistRepository",
    "SqlAlchemyPlaylistItemRepository",
    "SqlAlchemyScreenPlaylistAssignmentRepository",
    "SqlAlchemyScreenSyncStateRepository",
    "SqlAlchemyAuditLogRepository",
]
