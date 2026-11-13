from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError, InvalidStateTransition
from domain.value_object import MediaStatus, MediaType


@dataclass
class MediaAsset:
    """Metadata for an image or video stored in object storage."""

    name: str
    media_type: MediaType
    mime_type: str
    storage_path: str
    file_size: int
    checksum: str
    user_id: UUID
    id: UUID = field(default_factory=uuid4)
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
    status: MediaStatus = MediaStatus.ACTIVE
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.storage_path.strip():
            raise DomainError("media name and storage_path are required")
        if self.file_size < 0:
            raise DomainError("file_size cannot be negative")
        if not self.checksum.strip():
            raise DomainError("checksum is required")
        if self.width is not None and self.width <= 0:
            raise DomainError("width must be positive")
        if self.height is not None and self.height <= 0:
            raise DomainError("height must be positive")
        if self.duration_seconds is not None and self.duration_seconds <= 0:
            raise DomainError("duration_seconds must be positive")
        validate_timestamp(self.created_at)
        validate_timestamp(self.updated_at)

    def is_active(self) -> bool:
        return self.status is MediaStatus.ACTIVE

    def mark_as_deleted(self) -> None:
        self.status = MediaStatus.DELETED
        self.updated_at = utc_now()

    def validate_playlist_compatibility(self) -> None:
        if not self.is_active():
            raise InvalidStateTransition("deleted media cannot be added to a playlist")
