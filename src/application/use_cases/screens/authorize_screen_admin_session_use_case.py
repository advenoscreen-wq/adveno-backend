"""Validate and touch a protected screen-admin session for a user action."""

import hashlib
from datetime import timedelta

from application.exceptions.screen import ExpiredScreenAdminSessionError
from application.use_cases.screens.results import ProtectedScreenAdminSession
from application.use_cases.screens.screen_device_auth import (
    authenticate_screen_device_with_credential,
)
from domain.entities.common import utc_now
from ports.repositories.screen_admin_session_repository import ScreenAdminSessionRepository
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository

ADMIN_SESSION_INACTIVITY_TIMEOUT = timedelta(minutes=5)


class AuthorizeScreenAdminSessionUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        credential_repository: ScreenCredentialRepository,
        admin_session_repository: ScreenAdminSessionRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._credential_repository = credential_repository
        self._admin_session_repository = admin_session_repository

    async def __call__(self, *, credential: str, session_token: str) -> ProtectedScreenAdminSession:
        screen, screen_credential = await authenticate_screen_device_with_credential(
            credential=credential,
            screen_repository=self._screen_repository,
            credential_repository=self._credential_repository,
        )
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        admin_session = await self._admin_session_repository.get_by_screen_id_and_token_hash(
            screen.id,
            token_hash,
            for_update=True,
        )
        now = utc_now()
        if admin_session is None or not admin_session.is_active(
            idle_timeout=ADMIN_SESSION_INACTIVITY_TIMEOUT,
            at=now,
        ):
            raise ExpiredScreenAdminSessionError()

        admin_session.record_activity(at=now)
        await self._admin_session_repository.update(admin_session)
        return ProtectedScreenAdminSession(
            screen=screen,
            credential=screen_credential,
            admin_session=admin_session,
        )
