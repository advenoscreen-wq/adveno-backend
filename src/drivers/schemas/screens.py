"""Schemas for user-managed screen operations."""

from datetime import datetime
from uuid import UUID

from pydantic import (
    AliasPath,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

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
    desired_revision: int


class ScreenCredentialVerificationResponse(BaseModel):
    valid: bool


class ScreenSyncAcknowledgmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applied_revision: int = Field(ge=0)


class CreateScreenAdminSessionResponse(BaseModel):
    session_id: UUID
    pin: str = Field(pattern=r"^\d{6}$")
    expires_at: AwareDatetime


class VerifyScreenAdminSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pin: str = Field(pattern=r"^\d{6}$")


class VerifyScreenAdminSessionResponse(BaseModel):
    session_id: UUID
    session_token: str
    expires_at: AwareDatetime


class ScreenPlaybackEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    playlist_id: UUID
    playlist_item_id: UUID
    media_asset_id: UUID
    playlist_version: int = Field(ge=1)
    media_checksum: str = Field(min_length=1, max_length=255)
    played_at: AwareDatetime
    played_complete_at: AwareDatetime | None = None

    @field_validator("media_checksum")
    @classmethod
    def validate_checksum(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("media_checksum cannot be blank")
        return value

    @field_validator("played_complete_at")
    @classmethod
    def validate_completion_time(
        cls, value: AwareDatetime | None, info: ValidationInfo
    ) -> AwareDatetime | None:
        played_at = info.data.get("played_at")
        if value is not None and played_at is not None and value < played_at:
            raise ValueError("played_complete_at cannot precede played_at")
        return value


class ReportScreenPlaybackEventsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events: list[ScreenPlaybackEventRequest] = Field(min_length=1, max_length=100)


class ReportScreenPlaybackEventsResponse(BaseModel):
    stored_count: int = Field(ge=0)
    duplicate_count: int = Field(ge=0)


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


class PlaylistSummaryResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    version: int


class AssignedScreenPlaylistResponse(BaseModel):
    playlist: PlaylistSummaryResponse | None
    items: list[ScreenPlaylistItemResponse]
