"""Application orchestration for the BFF OAuth flow."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import asdict
from uuid import UUID

from application.dtos.oauth import OAuthLoginAttempt
from domain import User
from ports.repositories.user_repository import UserRepository
from ports.services.cache_service import CacheService
from ports.services.oauth_provider import OAuthProvider


class BFFAuthenticationService:
    def __init__(
        self,
        *,
        provider: OAuthProvider,
        user_repository: UserRepository,
        cache_service: CacheService,
        session_secret: str,
        state_ttl_seconds: int = 600,
        session_ttl_seconds: int = 3600,
    ) -> None:
        self.provider = provider
        self.user_repository = user_repository
        self.cache_service = cache_service
        self.session_secret = session_secret.encode()
        self.state_ttl_seconds = state_ttl_seconds
        self.session_ttl_seconds = session_ttl_seconds

    async def begin_login(self, redirect_uri: str) -> str:
        state = secrets.token_urlsafe(32)
        attempt = OAuthLoginAttempt(state, redirect_uri, time.time())
        await self.cache_service.set(
            self._state_key(state),
            json.dumps(asdict(attempt)),
            ttl_seconds=self.state_ttl_seconds,
        )
        return await self.provider.get_authorization_url(
            redirect_uri=redirect_uri,
            state=state,
        )

    async def complete_login(self, *, code: str, state: str) -> str:
        raw_attempt = await self.cache_service.pop(self._state_key(state))
        attempt = self._decode_attempt(raw_attempt)
        if attempt is None:
            raise ValueError("invalid or expired OAuth state")
        tokens = await self.provider.exchange_code(code, redirect_uri=attempt.redirect_uri)
        identity = await self.provider.get_user_info(tokens.access_token)
        try:
            user_id = UUID(identity.provider_user_id)
        except ValueError as error:
            raise ValueError("provider identity is not a valid application user ID") from error
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            user = await self.user_repository.save(User(id=user_id))
        if not user.is_active:
            raise ValueError("application user is inactive")
        return self._create_session(user.id)

    @staticmethod
    def _state_key(state: str) -> str:
        return f"oauth:state:{state}"

    @staticmethod
    def _decode_attempt(value: str | None) -> OAuthLoginAttempt | None:
        if value is None:
            return None
        try:
            payload = json.loads(value)
            return OAuthLoginAttempt(
                state=str(payload["state"]),
                redirect_uri=str(payload["redirect_uri"]),
                created_at=float(payload["created_at"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def _create_session(self, user_id: UUID) -> str:
        payload = {
            "sub": str(user_id),
            "exp": int(time.time()) + self.session_ttl_seconds,
        }
        encoded = _encode(payload)
        signature = hmac.new(self.session_secret, encoded.encode(), hashlib.sha256).digest()
        return f"{encoded}.{_base64url(signature)}"


def _encode(payload: dict[str, object]) -> str:
    return _base64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()
