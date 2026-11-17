"""Schemas for user-managed screen operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.value_object import ScreenStatus
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
