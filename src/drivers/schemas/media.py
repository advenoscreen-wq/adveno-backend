"""Schemas for media endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    id: UUID
    name: str
    media_type: MediaType
    mime_type: str
    storage_path: str
    file_size: int
    checksum: str
    width: int | None
    height: int | None
    duration_seconds: int | None
    status: MediaStatus
    created_at: datetime
    media_url: str


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
            if any(
                value is None
                for value in (
                    self.media_type,
                    self.mime_type,
                    self.storage_path,
                    self.file_size,
                )
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
    screen_id: UUID
    desired_revision: int


class UpdateMediaAndSyncResponse(MediaAssetResponse):
    screen_sync: list[ScreenSyncRevision]
