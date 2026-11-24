"""Revoke the current TV's protected settings session."""

from application.use_cases.screens.results import ProtectedScreenAdminSession
from domain.entities.common import utc_now
from ports.repositories.screen_admin_session_repository import ScreenAdminSessionRepository


class RevokeScreenAdminSessionUseCase:
    def __init__(self, *, admin_session_repository: ScreenAdminSessionRepository) -> None:
        self._admin_session_repository = admin_session_repository

    async def __call__(self, authorization: ProtectedScreenAdminSession) -> None:
        authorization.admin_session.revoke(at=utc_now())
        await self._admin_session_repository.update(authorization.admin_session)
