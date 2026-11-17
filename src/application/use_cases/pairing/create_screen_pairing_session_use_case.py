"""Create a short-lived screen pairing request."""

import hashlib
import secrets
from datetime import timedelta

from application.use_cases.pairing.commands import CreateScreenPairingSessionCommand
from application.use_cases.pairing.results import CreateScreenPairingSessionResult
from domain import ScreenPairingSession
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)


class CreateScreenPairingSessionUseCase:
    """Issue a one-time pairing token and persist only its digest."""

    def __init__(self, *, repository: ScreenPairingSessionRepository) -> None:
        self._repository = repository

    async def __call__(
        self, command: CreateScreenPairingSessionCommand
    ) -> CreateScreenPairingSessionResult:
        pairing_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(pairing_token.encode("utf-8")).hexdigest()
        session = ScreenPairingSession.create(
            token_hash=token_hash,
            ttl=timedelta(minutes=10),
            pairing_type=command.pairing_type,
        )
        persisted_session = await self._repository.save(session)
        return CreateScreenPairingSessionResult(
            session_id=persisted_session.id,
            pairing_token=pairing_token,
            expires_at=persisted_session.expires_at,
        )
