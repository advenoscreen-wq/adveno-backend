"""Verify a scanned pairing session for an authenticated dashboard user."""

import hashlib

from application.exceptions.pairing import PairingSessionNotFoundError
from application.use_cases.pairing.commands import VerifyScreenPairingSessionCommand
from application.use_cases.pairing.results import VerifyScreenPairingSessionResult
from domain.value_object import PairingSessionStatus
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)


class VerifyScreenPairingSessionUseCase:
    def __init__(self, *, repository: ScreenPairingSessionRepository) -> None:
        self._repository = repository

    async def __call__(
        self, command: VerifyScreenPairingSessionCommand
    ) -> VerifyScreenPairingSessionResult:
        token_hash = hashlib.sha256(command.pairing_token.encode("utf-8")).hexdigest()
        session = await self._repository.get_by_token_hash(token_hash)
        if session is None:
            raise PairingSessionNotFoundError()

        status = session.status
        if (
            status in (PairingSessionStatus.PENDING, PairingSessionStatus.CONNECTING)
            and session.is_expired()
        ):
            status = PairingSessionStatus.EXPIRED
        return VerifyScreenPairingSessionResult(
            session_id=session.id,
            status=status,
            pairing_type=session.pairing_type,
            screen_id=session.screen_id,
            screen_exists=session.screen_id is not None,
            expires_at=session.expires_at,
            created_at=session.created_at,
        )
