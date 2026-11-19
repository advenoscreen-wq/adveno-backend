"""Pairing application exceptions."""

from application.common.exceptions import AppError


class PairingSessionNotFoundError(AppError):
    """Raised when a pairing session is missing or its token is invalid."""

    def __init__(self) -> None:
        super().__init__(
            "Pairing session was not found.",
            code="PAIRING_SESSION_NOT_FOUND",
            status_code=404,
        )


class PairingSessionExpiredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Pairing session has expired.",
            code="PAIRING_SESSION_EXPIRED",
            status_code=410,
        )


class PairingSessionAlreadyCompletedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Pairing session is not pending.",
            code="PAIRING_SESSION_NOT_PENDING",
            status_code=409,
        )


class PairingSessionNotPairedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Pairing session must be connecting before it can be completed.",
            code="PAIRING_SESSION_NOT_PAIRED",
            status_code=409,
        )


class PairingOwnerNotSetError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "The pairing session has no approved screen owner. Start a new pairing session.",
            code="PAIRING_OWNER_NOT_SET",
            status_code=409,
        )


class PairingScreenAlreadyCreatedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "A screen has already been created for this pairing session.",
            code="PAIRING_SCREEN_ALREADY_CREATED",
            status_code=409,
        )


class PairingApprovalValidationError(AppError):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message, code=code, status_code=422)


class PairingScreenNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Screen was not found.",
            code="SCREEN_NOT_FOUND",
            status_code=404,
        )


class PairingScreenNotEligibleError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Screen is not eligible for reconnection.",
            code="SCREEN_NOT_ELIGIBLE",
            status_code=409,
        )
