"""Focused tests for provider-independent OAuth and BFF state handling."""

from uuid import uuid4

import httpx
import pytest

from adapters.services.oauth_service.supabase_oauth import SupabaseOAuthAdapter
from application.auth.oauth_service import BFFAuthenticationService
from application.dtos.oauth import OAuthTokenResult, OAuthUserInfo
from domain import User

USER_ID = uuid4()


class FakeProvider:
    async def get_authorization_url(self, *, redirect_uri: str, state: str, scopes=None) -> str:
        return f"https://provider.example/authorize?state={state}&redirect={redirect_uri}"

    async def exchange_code(self, code: str, *, redirect_uri: str) -> OAuthTokenResult:
        return OAuthTokenResult("access", "refresh", "bearer", 3600)

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResult:
        return OAuthTokenResult("new-access", "rotated-refresh", "bearer", 3600)

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        return OAuthUserInfo(str(USER_ID), "user@example.com", True)


class FakeUserRepository:
    def __init__(self) -> None:
        self.user: User | None = None

    async def get_by_id(self, user_id):
        return self.user

    async def save(self, user: User) -> User:
        self.user = user
        return user

    async def update(self, user: User) -> User:
        self.user = user
        return user


class FakeCacheService:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        self.values[key] = value

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def pop(self, key: str) -> str | None:
        return self.values.pop(key, None)


@pytest.mark.asyncio
async def test_bff_consumes_oauth_state_once() -> None:
    repository = FakeUserRepository()
    cache = FakeCacheService()
    service = BFFAuthenticationService(
        provider=FakeProvider(),
        user_repository=repository,
        cache_service=cache,
        session_secret="test-secret",
    )
    await service.begin_login("http://localhost/callback")
    state = next(iter(cache.values)).rsplit(":", maxsplit=1)[-1]

    session = await service.complete_login(code="code", state=state)

    assert session
    with pytest.raises(ValueError, match="invalid or expired"):
        await service.complete_login(code="code", state=state)


@pytest.mark.asyncio
async def test_supabase_refresh_preserves_rotated_refresh_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = SupabaseOAuthAdapter(
        supabase_url="https://project.supabase.co",
        supabase_anon_key="anon",
    )

    async def fake_request(method: str, path: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "rotated-refresh",
                "token_type": "bearer",
                "expires_in": 3600,
            },
        )

    monkeypatch.setattr(adapter, "_request", fake_request)
    result = await adapter.refresh_access_token("old-refresh")
    assert result.refresh_token == "rotated-refresh"
