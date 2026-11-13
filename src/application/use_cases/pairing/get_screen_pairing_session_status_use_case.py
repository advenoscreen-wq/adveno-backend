"""Read the state of a pairing session using its one-time token."""

import hashlib
import hmac

from application.exceptions.pairing import PairingSessionNotFoundError
from application.use_cases.pairing.commands import GetScreenPairingSessionStatusCommand
from application.use_cases.pairing.results import GetScreenPairingSessionStatusResult
from domain.value_object import PairingSessionStatus
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)


class GetScreenPairingSessionStatusUseCase:
    def __init__(self, *, repository: ScreenPairingSessionRepository) -> None:
        self._repository = repository

    async def __call__(
        self, command: GetScreenPairingSessionStatusCommand
    ) -> GetScreenPairingSessionStatusResult:
        session = await self._repository.get_by_id(command.session_id)
        token_hash = hashlib.sha256(command.pairing_token.encode("utf-8")).hexdigest()
        if session is None or not hmac.compare_digest(session.token_hash, token_hash):
            raise PairingSessionNotFoundError()

        status = session.status
        if status is PairingSessionStatus.PENDING and session.is_expired():
            status = PairingSessionStatus.EXPIRED
        return GetScreenPairingSessionStatusResult(status=status)
