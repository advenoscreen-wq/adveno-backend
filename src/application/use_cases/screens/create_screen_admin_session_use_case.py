"""Generate a one-time PIN for protected settings on an owned screen."""

import secrets
from datetime import timedelta

from application.exceptions.screen import ScreenDisconnectedError, ScreenNotFoundError
from application.use_cases.screens.commands import CreateScreenAdminSessionCommand
from application.use_cases.screens.results import CreateScreenAdminSessionResult
from domain import ScreenAdminSession
from domain.entities.common import utc_now
from ports.repositories.screen_admin_session_repository import ScreenAdminSessionRepository
from ports.repositories.screen_repository import ScreenRepository
from ports.services.pin_hasher import PinHasher

PIN_TTL = timedelta(minutes=5)


class CreateScreenAdminSessionUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        admin_session_repository: ScreenAdminSessionRepository,
        pin_hasher: PinHasher,
    ) -> None:
        self._screen_repository = screen_repository
        self._admin_session_repository = admin_session_repository
        self._pin_hasher = pin_hasher

    async def __call__(
        self, command: CreateScreenAdminSessionCommand
    ) -> CreateScreenAdminSessionResult:
        screen = await self._screen_repository.get_by_id(
            command.screen_id,
            user_id=command.user_id,
            for_update=True,
        )
        if screen is None:
            raise ScreenNotFoundError()
        if not screen.is_active:
            raise ScreenDisconnectedError()

        now = utc_now()
        pin = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = await self._pin_hasher.hash_pin(pin)
        await self._admin_session_repository.revoke_pending_by_screen_id(screen.id, at=now)
        session = await self._admin_session_repository.save(
            ScreenAdminSession(
                screen_id=screen.id,
                code_hash=code_hash,
                created_at=now,
                last_activity_at=now,
                expires_at=now + PIN_TTL,
            )
        )
        return CreateScreenAdminSessionResult(
            session_id=session.id,
            pin=pin,
            expires_at=session.expires_at,
        )
