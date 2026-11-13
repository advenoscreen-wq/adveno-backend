"""Issue a fresh screen credential after pairing has completed."""

import hashlib
import hmac
import secrets

from application.exceptions.pairing import (
    PairingCredentialNotAvailableError,
    PairingSessionNotFoundError,
    PairingSessionNotPairedError,
)
from application.use_cases.pairing.commands import IssuePairedScreenCredentialCommand
from application.use_cases.pairing.results import IssuePairedScreenCredentialResult
from domain.entities.screen_credential import ScreenCredential
from domain.value_object import PairingSessionStatus
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)


class IssuePairedScreenCredentialUseCase:
    def __init__(
        self,
        *,
        pairing_session_repository: ScreenPairingSessionRepository,
        screen_credential_repository: ScreenCredentialRepository,
    ) -> None:
        self._pairing_session_repository = pairing_session_repository
        self._screen_credential_repository = screen_credential_repository

    async def __call__(
        self, command: IssuePairedScreenCredentialCommand
    ) -> IssuePairedScreenCredentialResult:
        token_hash = hashlib.sha256(command.pairing_token.encode("utf-8")).hexdigest()
        session = await self._pairing_session_repository.get_by_id(
            command.session_id,
            for_update=True,
        )
        if session is None or not hmac.compare_digest(session.token_hash, token_hash):
            raise PairingSessionNotFoundError()
        if (
            session.status is not PairingSessionStatus.PAIRED
            or session.screen_id is None
            or session.paired_at is None
        ):
            raise PairingSessionNotPairedError()

        active_credential = (
            await self._screen_credential_repository.get_active_credential_by_screen(
                session.screen_id,
                for_update=True,
            )
        )
        if active_credential is None:
            raise PairingCredentialNotAvailableError()

        active_credential.revoke()
        await self._screen_credential_repository.update(active_credential)

        raw_credential = secrets.token_urlsafe(32)
        credential_hash = hashlib.sha256(raw_credential.encode("utf-8")).hexdigest()
        await self._screen_credential_repository.save(
            ScreenCredential(
                screen_id=session.screen_id,
                credential_hash=credential_hash,
            )
        )
        return IssuePairedScreenCredentialResult(
            screen_id=session.screen_id,
            credential=raw_credential,
        )
