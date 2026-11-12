"""Unit tests for meaningful domain rules."""

from datetime import timedelta
from uuid import uuid4

import pytest

from domain.entities.entities import (
    MediaAsset,
    Playlist,
    PlaylistItem,
    Screen,
    ScreenPairingSession,
    ScreenSyncState,
)
from domain.exceptions import DomainError, InvalidStateTransition
from domain.value_object.enums import MediaType, SyncStatus


def image_asset() -> MediaAsset:
    return MediaAsset(
        name="welcome",
        media_type=MediaType.IMAGE,
        mime_type="image/png",
        storage_path="media/welcome.png",
        file_size=10,
        checksum="checksum",
    )


def test_screen_deactivation_blocks_heartbeat() -> None:
    screen = Screen(screen_code="SCR-1", name="Lobby")
    screen.deactivate()

    with pytest.raises(InvalidStateTransition):
        screen.record_heartbeat()


def test_pairing_session_is_single_use() -> None:
    session = ScreenPairingSession.create(uuid4(), "hashed-token", timedelta(minutes=5))
    session.mark_as_paired()

    assert not session.is_valid()
    with pytest.raises(InvalidStateTransition):
        session.mark_as_paired()


def test_playlist_reorders_items_and_increments_version() -> None:
    playlist = Playlist(name="Lobby")
    first = PlaylistItem(playlist.id, uuid4(), 1)
    second = PlaylistItem(playlist.id, uuid4(), 2)
    playlist.items = [first, second]
    original_version = playlist.version

    playlist.reorder_items([second.id, first.id])

    assert [item.id for item in playlist.items] == [second.id, first.id]
    assert [item.position for item in playlist.items] == [1, 2]
    assert playlist.version == original_version + 1


def test_playlist_rejects_deleted_media() -> None:
    playlist = Playlist(name="Lobby")
    asset = image_asset()
    asset.mark_as_deleted()

    with pytest.raises(InvalidStateTransition):
        playlist.add_item(PlaylistItem(playlist.id, asset.id, 1), asset)


def test_sync_state_does_not_apply_non_desired_revision() -> None:
    state = ScreenSyncState(screen_id=uuid4(), desired_revision=2)
    state.mark_sync_started()

    with pytest.raises(DomainError):
        state.mark_sync_succeeded(1)

    assert state.sync_status is SyncStatus.SYNCING
