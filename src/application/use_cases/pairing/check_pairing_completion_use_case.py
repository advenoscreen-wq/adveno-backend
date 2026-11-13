"""Check that pairing is complete and has an active screen credential."""

import hashlib

from application.exceptions.pairing import PairingSessionNotFoundError
from application.use_cases.pairing.commands import CheckPairingCompletionCommand
from application.use_cases.pairing.results import CheckPairingCompletionResult
from domain.value_object import PairingSessionStatus
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)


class CheckPairingCompletionUseCase:
    def __init__(
        self,
        *,
        pairing_session_repository: ScreenPairingSessionRepository,
        screen_credential_repository: ScreenCredentialRepository,
    ) -> None:
        self._pairing_session_repository = pairing_session_repository
        self._screen_credential_repository = screen_credential_repository

    async def __call__(
        self, command: CheckPairingCompletionCommand
    ) -> CheckPairingCompletionResult:
        token_hash = hashlib.sha256(command.pairing_token.encode("utf-8")).hexdigest()
        session = await self._pairing_session_repository.get_by_token_hash(token_hash)
        if session is None:
            raise PairingSessionNotFoundError()

        has_active_credential = False
        if session.screen_id is not None:
            has_active_credential = (
                await self._screen_credential_repository.get_active_credential_by_screen(
                    session.screen_id
                )
            ) is not None

        completed = (
            session.status is PairingSessionStatus.PAIRED
            and session.screen_id is not None
            and session.paired_at is not None
            and has_active_credential
        )
        return CheckPairingCompletionResult(
            session_id=session.id,
            status=session.status,
            screen_id=session.screen_id,
            paired_at=session.paired_at,
            completed=completed,
        )
