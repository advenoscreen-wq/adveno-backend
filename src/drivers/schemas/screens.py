"""Schemas for user-managed screen operations."""

from datetime import datetime
from uuid import UUID

from pydantic import AliasPath, BaseModel, ConfigDict, Field, field_validator

from domain.value_object import MediaStatus, MediaType, ScreenStatus
from drivers.schemas.playlists import PlaylistResponse


class UpdateScreenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name cannot be blank")
        return normalized


class UpdateScreenResponse(BaseModel):
    id: UUID
    screen_code: str
    name: str
    status: ScreenStatus
    updated_at: datetime


class ScreenResponse(UpdateScreenResponse):
    assigned_playlist: PlaylistResponse | None


class ScreenListItemResponse(UpdateScreenResponse):
    device_model: str | None
    app_version: str | None
    last_seen_at: datetime | None
    last_successful_sync_at: datetime | None


class AssignPlaylistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    playlist_id: UUID


class ScreenPlaylistAssignmentResponse(BaseModel):
    id: UUID
    screen_id: UUID
    playlist_id: UUID
    assigned_at: datetime


class ScreenSyncCheckResponse(BaseModel):
    need_sync: bool


class ScreenPlaylistMediaResponse(BaseModel):
    id: UUID = Field(validation_alias=AliasPath("media", "id"))
    name: str = Field(validation_alias=AliasPath("media", "name"))
    media_type: MediaType = Field(validation_alias=AliasPath("media", "media_type"))
    mime_type: str = Field(validation_alias=AliasPath("media", "mime_type"))
    storage_path: str = Field(validation_alias=AliasPath("media", "storage_path"))
    file_size: int = Field(validation_alias=AliasPath("media", "file_size"))
    checksum: str = Field(validation_alias=AliasPath("media", "checksum"))
    width: int | None = Field(validation_alias=AliasPath("media", "width"))
    height: int | None = Field(validation_alias=AliasPath("media", "height"))
    duration_seconds: int | None = Field(validation_alias=AliasPath("media", "duration_seconds"))
    status: MediaStatus = Field(validation_alias=AliasPath("media", "status"))
    media_url: str


class ScreenPlaylistItemResponse(BaseModel):
    id: UUID = Field(validation_alias=AliasPath("item", "id"))
    position: int = Field(validation_alias=AliasPath("item", "position"))
    duration_seconds: int | None = Field(validation_alias=AliasPath("item", "duration_seconds"))
    media: ScreenPlaylistMediaResponse


class AssignedScreenPlaylistResponse(BaseModel):
    id: UUID = Field(validation_alias=AliasPath("playlist", "id"))
    name: str = Field(validation_alias=AliasPath("playlist", "name"))
    description: str | None = Field(validation_alias=AliasPath("playlist", "description"))
    version: int = Field(validation_alias=AliasPath("playlist", "version"))
    items: list[ScreenPlaylistItemResponse]
