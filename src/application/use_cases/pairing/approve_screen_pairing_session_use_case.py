
"""Approve a pending screen pairing request."""

import hashlib

from application.exceptions.pairing import (
    PairingApprovalValidationError,
    PairingScreenNotEligibleError,
    PairingScreenNotFoundError,
    PairingSessionAlreadyCompletedError,
    PairingSessionExpiredError,
    PairingSessionNotFoundError,
)
from application.use_cases.pairing.commands import ApproveScreenPairingSessionCommand
from application.use_cases.pairing.results import ApproveScreenPairingSessionResult
from domain.entities.screen_credential import ScreenCredential
from domain.entities.screen_pairing_session import ScreenPairingSession
from domain.value_object import PairingSessionStatus, PairingType
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)
from ports.repositories.screen_repository import ScreenRepository


class ApproveScreenPairingSessionUseCase:
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

    async def __call__(
        self, command: ApproveScreenPairingSessionCommand
    ) -> ApproveScreenPairingSessionResult:
        token_hash = hashlib.sha256(
            command.pairing_token.encode("utf-8")
        ).hexdigest()

        session = await self._pairing_session_repository.get_by_token_hash(
            token_hash,
            for_update=True,
        )

        if session is None:
            raise PairingSessionNotFoundError()

        self._validate_session(session)

        if session.pairing_type is PairingType.NEW_SCREEN:
            await self._approve_new_screen(command, session)
        else:
            await self._approve_existing_screen(
                command=command,
                session=session,
                token_hash=token_hash,
            )

        updated = await self._pairing_session_repository.update(session)

        paired_at = updated.paired_at
        pairing_type = updated.pairing_type

        if paired_at is None or pairing_type is None:
            raise PairingSessionAlreadyCompletedError()

        return ApproveScreenPairingSessionResult(
            session_id=updated.id,
            pairing_type=pairing_type,
            status=updated.status,
            screen_id=updated.screen_id,
            paired_at=paired_at,
        )

    @staticmethod
    def _validate_session(session: ScreenPairingSession) -> None:
        if session.status is PairingSessionStatus.EXPIRED:
            raise PairingSessionExpiredError()

        if session.status is not PairingSessionStatus.PENDING:
            raise PairingSessionAlreadyCompletedError()

        if session.is_expired():
            raise PairingSessionExpiredError()

        if session.pairing_type is None:
            raise PairingApprovalValidationError(
                "Pairing type has not been selected.",
                code="PAIRING_TYPE_REQUIRED",
            )

    async def _approve_new_screen(
        self,
        command: ApproveScreenPairingSessionCommand,
        session: ScreenPairingSession,
    ) -> None:
        if command.screen_id is not None:
            raise PairingApprovalValidationError(
                "NEW_SCREEN pairing does not accept a screen_id.",
                code="SCREEN_ID_NOT_ALLOWED",
            )

        session.mark_as_paired()

    async def _approve_existing_screen(
        self,
        *,
        command: ApproveScreenPairingSessionCommand,
        session: ScreenPairingSession,
        token_hash: str,
    ) -> None:
        if command.screen_id is None:
            raise PairingApprovalValidationError(
                "screen_id is required for RECONNECT_EXISTING pairing.",
                code="SCREEN_ID_REQUIRED",
            )

        screen = await self._screen_repository.get_by_id(
            command.screen_id,
            user_id=command.user_id,
        )

        if screen is None:
            raise PairingScreenNotFoundError()

        if not screen.is_active:
            raise PairingScreenNotEligibleError()

        active_credential = (
            await self._screen_credential_repository.get_active_credential_by_screen(
                screen.id,
                for_update=True,
            )
        )

        if active_credential is not None:
            active_credential.revoke()
            await self._screen_credential_repository.update(active_credential)

        await self._screen_credential_repository.save(
            ScreenCredential(
                screen_id=screen.id,
                credential_hash=token_hash,
            )
        )

        session.mark_as_paired(screen_id=screen.id)
