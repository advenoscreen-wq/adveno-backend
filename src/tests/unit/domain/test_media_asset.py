"""Unit tests for media asset validity and lifecycle."""

from uuid import uuid4

import pytest

from domain import MediaAsset
from domain.exceptions import DomainError, InvalidStateTransition
from domain.value_object import MediaStatus, MediaType


def make_image() -> MediaAsset:
    return MediaAsset(
        name="Welcome",
        media_type=MediaType.IMAGE,
        mime_type="image/png",
        storage_path="media/welcome.png",
        file_size=100,
        checksum="sha256-value",
        user_id=uuid4(),
        width=1920,
        height=1080,
    )


def test_valid_image_asset_is_active() -> None:
    asset = make_image()

    assert asset.is_active()
    assert asset.status is MediaStatus.ACTIVE


def test_deleted_asset_cannot_be_added_to_playlist() -> None:
    asset = make_image()
    asset.mark_as_deleted()

    assert not asset.is_active()
    assert asset.status is MediaStatus.DELETED
    with pytest.raises(InvalidStateTransition):
        asset.validate_playlist_compatibility()


def test_media_asset_rejects_negative_file_size() -> None:
    with pytest.raises(DomainError, match="file_size cannot be negative"):
        MediaAsset(
            name="Welcome",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            storage_path="media/welcome.png",
            file_size=-1,
            checksum="sha256-value",
            user_id=uuid4(),
        )


def test_media_asset_rejects_nonpositive_dimensions() -> None:
    with pytest.raises(DomainError, match="width must be positive"):
        MediaAsset(
            name="Welcome",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            storage_path="media/welcome.png",
            file_size=10,
            checksum="sha256-value",
            user_id=uuid4(),
            width=0,
        )
