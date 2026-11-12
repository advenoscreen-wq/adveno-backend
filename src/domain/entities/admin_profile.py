from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from domain.entities.common import utc_now, validate_timestamp


@dataclass
class AdminProfile:
    """Application profile linked to a Supabase Auth user."""

    id: UUID
    is_active: bool = True
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        validate_timestamp(self.created_at)
        validate_timestamp(self.updated_at)
