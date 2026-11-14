"""Unit tests for playlist item constraints."""

from uuid import uuid4

import pytest

from domain import PlaylistItem
from domain.exceptions import DomainError


def test_playlist_item_updates_position_and_duration() -> None:
    item = PlaylistItem(playlist_id=uuid4(), media_asset_id=uuid4(), position=1)

    item.update_position(3)
    item.update_duration(12)

    assert item.position == 3
    assert item.duration_seconds == 12


def test_playlist_item_rejects_nonpositive_position() -> None:
    with pytest.raises(DomainError, match="position must be positive"):
        PlaylistItem(playlist_id=uuid4(), media_asset_id=uuid4(), position=0)


def test_playlist_item_rejects_nonpositive_duration() -> None:
    with pytest.raises(DomainError, match="duration must be positive"):
        PlaylistItem(
            playlist_id=uuid4(),
            media_asset_id=uuid4(),
            position=1,
            duration_seconds=0,
        )
