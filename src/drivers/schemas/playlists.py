"""Schemas for playlist management endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreatePlaylistItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_asset_id: UUID
    position: int = Field(ge=1)
    duration_seconds: int | None = Field(default=None, gt=0)


class CreatePlaylistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    items: list[CreatePlaylistItemRequest] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_positions_are_unique(self) -> "CreatePlaylistRequest":
        positions = [item.position for item in self.items]
        if len(positions) != len(set(positions)):
            raise ValueError("item positions must be unique")
        return self


class UpdatePlaylistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    items: list[CreatePlaylistItemRequest] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_positions_are_unique(self) -> "UpdatePlaylistRequest":
        positions = [item.position for item in self.items]
        if len(positions) != len(set(positions)):
            raise ValueError("item positions must be unique")
        return self


class PlaylistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    media_asset_id: UUID
    position: int
    duration_seconds: int | None


class PlaylistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    version: int
    created_at: datetime
    items: list[PlaylistItemResponse]

    @classmethod
    def from_entity(cls, playlist: object) -> "PlaylistResponse":
        return cls.model_validate(playlist, from_attributes=True)
