"""Schemas for user-managed screen operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.value_object import ScreenStatus


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
