"""Schemas for media endpoints."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from domain.value_object import MediaStatus, MediaType


class RequestMediaUploadUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_name: str = Field(min_length=1, max_length=255)

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, value: str) -> str:
        value = value.strip()
        if value in {".", ".."} or "/" in value or "\\" in value or "\x00" in value:
            raise ValueError("file_name must be a file name, not a path")
        return value


class RequestMediaUploadUrlResponse(BaseModel):
    signed_url: str
    storage_path: str


class CreateMediaAssetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    media_type: MediaType
    mime_type: str = Field(min_length=1, max_length=100)
    storage_path: str = Field(min_length=1, max_length=1024)
    file_size: int = Field(ge=0)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    duration_seconds: int | None = Field(default=None, gt=0)

    @field_validator("name", "mime_type", "storage_path")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value cannot be blank")
        return value.strip()

    @model_validator(mode="after")
    def validate_mime_type_matches_media_type(self) -> "CreateMediaAssetRequest":
        expected_prefix = "image/" if self.media_type is MediaType.IMAGE else "video/"
        if not self.mime_type.lower().startswith(expected_prefix):
            raise ValueError("mime_type must match media_type")
        return self


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    created_at: datetime = Field(validation_alias=AliasPath("media", "created_at"))
    media_url: str

    @classmethod
    def from_result(cls, result: object) -> Self:
        return cls.model_validate(result, from_attributes=True)


class UpdateMediaAndSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_replaced: bool
    name: str = Field(min_length=1, max_length=255)
    media_type: MediaType | None = None
    mime_type: str | None = Field(default=None, min_length=1, max_length=100)
    storage_path: str | None = Field(default=None, min_length=1, max_length=1024)
    file_size: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    duration_seconds: int | None = Field(default=None, gt=0)

    @field_validator("name", "mime_type", "storage_path")
    @classmethod
    def strip_non_blank_values(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("value cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_update_fields(self) -> "UpdateMediaAndSyncRequest":
        file_fields = (
            self.media_type,
            self.mime_type,
            self.storage_path,
            self.file_size,
            self.width,
            self.height,
            self.duration_seconds,
        )
        if self.is_replaced:
            if (
                self.media_type is None
                or self.mime_type is None
                or self.storage_path is None
                or self.file_size is None
            ):
                raise ValueError("replacement requires media file metadata")
            prefix = "image/" if self.media_type is MediaType.IMAGE else "video/"
            if (
                not self.mime_type.lower().startswith(prefix)
                or not self.mime_type[len(prefix) :].strip()
            ):
                raise ValueError("mime_type must match media_type")
        elif any(value is not None for value in file_fields):
            raise ValueError("metadata updates require a name only")
        return self


class ScreenSyncRevision(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    screen_id: UUID
    desired_revision: int


class UpdateMediaAndSyncResponse(MediaAssetResponse):
    screen_sync: list[ScreenSyncRevision] = Field(validation_alias="sync_states")
