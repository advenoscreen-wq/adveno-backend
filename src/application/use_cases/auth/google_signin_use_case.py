"""Use case for requesting Google OAuth sign-in."""

import base64
import hashlib
import json
import secrets
import time
from dataclasses import asdict

from application.dtos.oauth import OAuthLoginAttempt
from application.use_cases.auth.commands import GoogleSigninCommand
from application.use_cases.auth.results import GoogleSigninResult
from ports.services.cache_service import CacheService
from ports.services.oauth_provider import OAuthProvider


class GoogleSigninUseCase:
    def __init__(
        self,
        *,
        provider: OAuthProvider,
        cache_service: CacheService,
        state_ttl_seconds: int,
    ) -> None:
        self._provider = provider
        self._cache_service = cache_service
        self._state_ttl_seconds = state_ttl_seconds

    async def __call__(self, command: GoogleSigninCommand) -> GoogleSigninResult:
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("ascii")).digest())
            .rstrip(b"=")
            .decode("ascii")
        )
        attempt = OAuthLoginAttempt(state, command.redirect_uri, time.time(), code_verifier)
        await self._cache_service.set(
            f"oauth:state:{state}",
            json.dumps(asdict(attempt)),
            ttl_seconds=self._state_ttl_seconds,
        )
        authorization_url = await self._provider.get_authorization_url(
            redirect_uri=command.redirect_uri,
            code_challenge=code_challenge,
        )
        return GoogleSigninResult(authorization_url=authorization_url, state=state)
