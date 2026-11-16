"""Unit tests for playlist membership and ordering rules."""

from uuid import UUID, uuid4

import pytest

from domain import MediaAsset, Playlist, PlaylistItem
from domain.exceptions import DomainError
from domain.value_object import MediaType


def make_media(user_id: UUID) -> MediaAsset:
    return MediaAsset(
        name="Welcome",
        media_type=MediaType.IMAGE,
        mime_type="image/png",
        storage_path="media/welcome.png",
        file_size=10,
        checksum="checksum",
        user_id=user_id,
    )


def test_adding_owned_media_sorts_items_and_increments_version() -> None:
    user_id = uuid4()
    playlist = Playlist(name="Lobby", user_id=user_id)
    first = PlaylistItem(playlist.id, uuid4(), 1)
    second = PlaylistItem(playlist.id, uuid4(), 2)
    original_version = playlist.version

    playlist.add_item(second, make_media(user_id))
    playlist.add_item(first, make_media(user_id))

    assert [item.position for item in playlist.items] == [1, 2]
    assert playlist.version == original_version + 2


def test_playlist_rejects_media_owned_by_another_user() -> None:
    playlist = Playlist(name="Lobby", user_id=uuid4())
    item = PlaylistItem(playlist.id, uuid4(), 1)

    with pytest.raises(DomainError, match="different user"):
        playlist.add_item(item, make_media(uuid4()))

    assert playlist.items == []


def test_playlist_rejects_duplicate_item_position() -> None:
    user_id = uuid4()
    playlist = Playlist(name="Lobby", user_id=user_id)
    playlist.add_item(PlaylistItem(playlist.id, uuid4(), 1), make_media(user_id))

    with pytest.raises(DomainError, match="position must be unique"):
        playlist.add_item(PlaylistItem(playlist.id, uuid4(), 1), make_media(user_id))

    assert len(playlist.items) == 1


def test_reordering_items_updates_positions() -> None:
    playlist = Playlist(name="Lobby", user_id=uuid4())
    first = PlaylistItem(playlist.id, uuid4(), 1)
    second = PlaylistItem(playlist.id, uuid4(), 2)
    playlist.items = [first, second]

    playlist.reorder_items([second.id, first.id])

    assert playlist.items == [second, first]
    assert [item.position for item in playlist.items] == [1, 2]


def test_reordering_rejects_incomplete_item_list() -> None:
    playlist = Playlist(name="Lobby", user_id=uuid4())
    first = PlaylistItem(playlist.id, uuid4(), 1)
    second = PlaylistItem(playlist.id, uuid4(), 2)
    playlist.items = [first, second]

    with pytest.raises(DomainError, match="every playlist item exactly once"):
        playlist.reorder_items([first.id])


def test_removing_missing_item_is_rejected() -> None:
    playlist = Playlist(name="Lobby", user_id=uuid4())

    with pytest.raises(DomainError, match="item was not found"):
        playlist.remove_item(uuid4())


def test_playlist_rejects_blank_name() -> None:
    with pytest.raises(DomainError, match="playlist name is required"):
        Playlist(name="  ", user_id=uuid4())
