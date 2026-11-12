"""Application exception foundation."""


class ApplicationError(Exception):
    """Base class for expected application failures."""

    def __init__(self, message: str, code: str) -> None:
        self.message = message
        self.code = code
        super().__init__(message)
