from enum import StrEnum


class UserRole(StrEnum):
    """Roles supported by the Adveno application."""

    ADMIN = "ADMIN"
    USER = "USER"
