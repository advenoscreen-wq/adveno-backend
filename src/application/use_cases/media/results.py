"""Results returned by media use cases."""

from dataclasses import dataclass

from domain import MediaAsset, ScreenSyncState


@dataclass(frozen=True)
class RequestMediaUploadUrlResult:
    signed_url: str
    storage_path: str


@dataclass(frozen=True)
class RequestMediaReplacementUploadUrlResult:
    signed_url: str
    storage_path: str


@dataclass(frozen=True)
class CreateMediaAssetResult:
    media: MediaAsset
    media_url: str


@dataclass(frozen=True)
class MediaAssetWithUrl:
    media: MediaAsset
    media_url: str


@dataclass(frozen=True)
class UpdateMediaAndSyncResult:
    media: MediaAsset
    media_url: str
    sync_states: list[ScreenSyncState]


@dataclass(frozen=True)
class ListMediaAssetsResult:
    items: list[MediaAssetWithUrl]
    total_pages: int
    total_items: int
    has_next: bool
    has_prev: bool
    limit: int
    page: int
