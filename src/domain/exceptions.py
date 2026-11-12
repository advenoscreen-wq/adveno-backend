"""Domain errors raised when business invariants are violated."""


class DomainError(ValueError):
    """Base class for invalid domain state or operations."""


class InvalidStateTransition(DomainError):
    """Raised when an entity cannot perform the requested transition."""


class PersistenceError(Exception):
    """Base class for persistence boundary failures."""


class PersistenceConflictError(PersistenceError):
    """Raised when persistence detects a uniqueness or integrity conflict."""
