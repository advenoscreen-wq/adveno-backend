"""Representative PostgreSQL coverage for all domain repositories."""

from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.domain_repositories import (
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
from domain.value_object.enums import MediaType


@pytest.mark.integration
async def test_all_domain_repositories_round_trip_entities(
    integration_session: AsyncSession,
) -> None:
    admin = AdminProfile(id=uuid4())
    screen = Screen(screen_code="SCR-1", name="Lobby")
    media = MediaAsset(
        name="welcome",
        media_type=MediaType.IMAGE,
        mime_type="image/png",
        storage_path="media/welcome.png",
        file_size=10,
        checksum="checksum",
    )
    playlist = Playlist(name="Lobby playlist")

    await SqlAlchemyAdminProfileRepository(integration_session).save(admin)
    await SqlAlchemyScreenRepository(integration_session).save(screen)
    await SqlAlchemyMediaAssetRepository(integration_session).save(media)
    await SqlAlchemyPlaylistRepository(integration_session).save(playlist)

    pairing = ScreenPairingSession.create(screen.id, "pairing-hash", timedelta(minutes=5))
    credential = ScreenCredential(screen_id=screen.id, credential_hash="credential-hash")
    item = PlaylistItem(playlist_id=playlist.id, media_asset_id=media.id, position=1)
    assignment = ScreenPlaylistAssignment(screen_id=screen.id, playlist_id=playlist.id)
    sync_state = ScreenSyncState(screen_id=screen.id)
    audit = AuditLog(action="SCREEN_REGISTERED", admin_id=admin.id, screen_id=screen.id)

    await SqlAlchemyScreenPairingSessionRepository(integration_session).save(pairing)
    await SqlAlchemyScreenCredentialRepository(integration_session).save(credential)
    await SqlAlchemyPlaylistItemRepository(integration_session).save(item)
    await SqlAlchemyScreenPlaylistAssignmentRepository(integration_session).save(assignment)
    await SqlAlchemyScreenSyncStateRepository(integration_session).save(sync_state)
    await SqlAlchemyAuditLogRepository(integration_session).save(audit)

    assert await SqlAlchemyAdminProfileRepository(integration_session).get_by_id(admin.id)
    assert await SqlAlchemyScreenPairingSessionRepository(integration_session).get_by_id(pairing.id)
    assert await SqlAlchemyScreenCredentialRepository(integration_session).get_by_id(credential.id)
    assert await SqlAlchemyMediaAssetRepository(integration_session).get_by_id(media.id)
    assert await SqlAlchemyPlaylistRepository(integration_session).get_by_id(playlist.id)
    assert await SqlAlchemyPlaylistItemRepository(integration_session).list_by_playlist_id(
        playlist.id
    )
    assert await SqlAlchemyScreenPlaylistAssignmentRepository(
        integration_session
    ).get_active_by_screen_id(screen.id)
    assert await SqlAlchemyScreenSyncStateRepository(integration_session).get_by_screen_id(
        screen.id
    )
    assert await SqlAlchemyAuditLogRepository(integration_session).list_by_screen_id(screen.id)
