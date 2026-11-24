"""Verify a screen's PIN and issue a short-lived settings-session token."""

import hashlib
import secrets
from datetime import timedelta

from application.exceptions.screen import (
    ExpiredScreenAdminSessionError,
    InvalidScreenAdminPinError,
    ScreenAdminPinRateLimitError,
)
from application.use_cases.screens.commands import VerifyScreenAdminSessionCommand
from application.use_cases.screens.results import VerifyScreenAdminSessionResult
from application.use_cases.screens.screen_device_auth import authenticate_screen_device
from domain.entities.common import utc_now
from ports.repositories.screen_admin_session_repository import ScreenAdminSessionRepository
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository
from ports.services.cache_service import CacheService
from ports.services.pin_hasher import PinHasher

PIN_ATTEMPT_LIMIT = 5
PIN_ATTEMPT_WINDOW_SECONDS = 600
ADMIN_SESSION_LIFETIME = timedelta(minutes=15)
ADMIN_SESSION_INACTIVITY_TIMEOUT = timedelta(minutes=5)


class VerifyScreenAdminSessionUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        credential_repository: ScreenCredentialRepository,
        admin_session_repository: ScreenAdminSessionRepository,
        pin_hasher: PinHasher,
        cache_service: CacheService,
    ) -> None:
        self._screen_repository = screen_repository
        self._credential_repository = credential_repository
        self._admin_session_repository = admin_session_repository
        self._pin_hasher = pin_hasher
        self._cache_service = cache_service

    async def __call__(
        self,
        *,
        credential: str,
        command: VerifyScreenAdminSessionCommand,
    ) -> VerifyScreenAdminSessionResult:
        screen = await authenticate_screen_device(
            credential=credential,
            screen_repository=self._screen_repository,
            credential_repository=self._credential_repository,
        )
        rate_limit_key = f"screen-admin:pin-attempts:{screen.id}"
        attempt = await self._cache_service.increment_with_ttl(
            rate_limit_key,
            ttl_seconds=PIN_ATTEMPT_WINDOW_SECONDS,
        )
        if attempt > PIN_ATTEMPT_LIMIT:
            raise ScreenAdminPinRateLimitError()

        session = await self._admin_session_repository.get_pending_pin_by_screen_id(
            screen.id,
            for_update=True,
        )
        now = utc_now()
        if session is None:
            raise InvalidScreenAdminPinError()
        if not session.can_verify_pin(at=now):
            session.revoke(at=now)
            await self._admin_session_repository.update(session)
            raise ExpiredScreenAdminSessionError()

        pin_matches = await self._pin_hasher.verify_pin(session.code_hash, command.pin)
        if not pin_matches:
            raise InvalidScreenAdminPinError()

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        session.activate(
            token_hash,
            absolute_ttl=ADMIN_SESSION_LIFETIME,
            at=now,
        )
        await self._admin_session_repository.update(session)
        await self._cache_service.delete(rate_limit_key)
        return VerifyScreenAdminSessionResult(
            session_id=session.id,
            session_token=raw_token,
            expires_at=session.expires_at,
        )
