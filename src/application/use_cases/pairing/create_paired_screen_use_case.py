"""Create a screen after a NEW_SCREEN pairing session is approved."""

import hashlib
import hmac
import secrets

from application.exceptions.pairing import (
    PairingApprovalValidationError,
    PairingScreenAlreadyCreatedError,
    PairingSessionExpiredError,
    PairingSessionNotFoundError,
    PairingSessionNotPairedError,
)
from application.use_cases.pairing.commands import CreatePairedScreenCommand
from application.use_cases.pairing.results import CreatePairedScreenResult
from domain.entities.screen import Screen
from domain.entities.screen_credential import ScreenCredential
from domain.value_object import PairingSessionStatus, PairingType
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)
from ports.repositories.screen_repository import ScreenRepository


class CreatePairedScreenUseCase:
    def __init__(
        self,
        *,
        pairing_session_repository: ScreenPairingSessionRepository,
        screen_repository: ScreenRepository,
        screen_credential_repository: ScreenCredentialRepository,
    ) -> None:
        self._pairing_session_repository = pairing_session_repository
        self._screen_repository = screen_repository
        self._screen_credential_repository = screen_credential_repository

    async def __call__(self, command: CreatePairedScreenCommand) -> CreatePairedScreenResult:
        token_hash = hashlib.sha256(command.pairing_token.encode("utf-8")).hexdigest()
        session = await self._pairing_session_repository.get_by_id(
            command.session_id,
            for_update=True,
        )
        if session is None or not hmac.compare_digest(session.token_hash, token_hash):
            raise PairingSessionNotFoundError()
        if session.status is PairingSessionStatus.EXPIRED:
            raise PairingSessionExpiredError()
        if session.status is not PairingSessionStatus.PAIRED:
            if session.is_expired():
                raise PairingSessionExpiredError()
            raise PairingSessionNotPairedError()
        if session.pairing_type is not PairingType.NEW_SCREEN:
            raise PairingApprovalValidationError(
                "Only NEW_SCREEN pairing sessions can create a screen.",
                code="NEW_SCREEN_PAIRING_REQUIRED",
            )
        if session.screen_id is not None:
            raise PairingScreenAlreadyCreatedError()

        screen = await self._screen_repository.save(
            Screen(
                user_id=command.user_id,
                name=command.name,
                device_model=command.device_model,
                app_version=command.app_version,
            )
        )
        raw_credential = secrets.token_urlsafe(32)
        credential_hash = hashlib.sha256(raw_credential.encode("utf-8")).hexdigest()
        await self._screen_credential_repository.save(
            ScreenCredential(
                screen_id=screen.id,
                credential_hash=credential_hash,
            )
        )
        session.assign_new_screen(screen.id)
        await self._pairing_session_repository.update(session)

        return CreatePairedScreenResult(
            screen_id=screen.id,
            screen_code=screen.screen_code,
            name=screen.name,
            credential=raw_credential,
        )
