from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from domain.entities.common import utc_now, validate_timestamp
from domain.exceptions import DomainError
from domain.value_object import UserRole


@dataclass
class User:
    """Application user linked to a Supabase Auth user."""

    id: UUID
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        try:
            self.role = UserRole(self.role)
        except (TypeError, ValueError) as error:
            raise DomainError("user role must be ADMIN or USER") from error
        validate_timestamp(self.created_at)
        validate_timestamp(self.updated_at)

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = utc_now()

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = utc_now()
