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


@dataclass(frozen=True)
class UpdateMediaAndSyncResult:
    media: MediaAsset
    sync_states: list[ScreenSyncState]
