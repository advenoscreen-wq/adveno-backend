"""Revoke the authenticated screen credential and protected settings session."""

from application.use_cases.screens.results import ProtectedScreenAdminSession
from domain.entities.common import utc_now
from ports.repositories.screen_admin_session_repository import ScreenAdminSessionRepository
from ports.repositories.screen_credential_repository import ScreenCredentialRepository


class LogoutScreenUseCase:
    def __init__(
        self,
        *,
        credential_repository: ScreenCredentialRepository,
        admin_session_repository: ScreenAdminSessionRepository,
    ) -> None:
        self._credential_repository = credential_repository
        self._admin_session_repository = admin_session_repository

    async def __call__(self, authorization: ProtectedScreenAdminSession) -> None:
        authorization.credential.revoke()
        authorization.admin_session.revoke(at=utc_now())
        await self._credential_repository.update(authorization.credential)
        await self._admin_session_repository.update(authorization.admin_session)
