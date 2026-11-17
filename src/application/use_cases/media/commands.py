"""Commands for media use cases."""

from dataclasses import dataclass
from uuid import UUID

from domain.value_object import MediaType


@dataclass(frozen=True)
class RequestMediaUploadUrlCommand:
    user_id: UUID
    file_name: str
    access_token: str


@dataclass(frozen=True)
class RequestMediaReplacementUploadUrlCommand:
    media_id: UUID
    user_id: UUID
    access_token: str


@dataclass(frozen=True)
class CreateMediaAssetCommand:
    user_id: UUID
    name: str
    media_type: MediaType
    mime_type: str
    storage_path: str
    file_size: int
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None


@dataclass(frozen=True)
class UpdateMediaAndSyncCommand:
    media_id: UUID
    user_id: UUID
    is_replaced: bool
    name: str | None = None
    media_type: MediaType | None = None
    mime_type: str | None = None
    storage_path: str | None = None
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
