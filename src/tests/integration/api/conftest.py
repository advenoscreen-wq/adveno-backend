"""Shared HTTP client and fakes for API integration tests."""

from collections.abc import AsyncIterator
from uuid import UUID

import httpx
import pytest
import pytest_asyncio

from application.dtos.oauth import OAuthTokenResult, OAuthUserInfo
from config.settings import Settings
from domain import User
from drivers.routers.auth.dependencies import get_user_repository
from drivers.core.app import create_app
from drivers.routers.dependencies import get_cache_service, get_oauth_provider


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}
        self.saved: list[User] = []
        self.updated: list[User] = []

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def save(self, user: User) -> User:
        self.users[user.id] = user
        self.saved.append(user)
        return user

    async def update(self, user: User) -> User:
        self.users[user.id] = user
        self.updated.append(user)
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


class FakeOAuthProvider:
    def __init__(self, refresh_token_calls: list[str]) -> None:
        self.refresh_token_calls = refresh_token_calls

    async def get_authorization_url(
        self,
        *,
        redirect_uri: str,
        code_challenge: str | None = None,
        scopes: list[str] | None = None,
    ) -> str:
        return (
            "https://provider.example/authorize?"
            f"code_challenge={code_challenge}&code_challenge_method=s256"
        )

    async def exchange_code(self, code: str, *, code_verifier: str) -> OAuthTokenResult:
        return OAuthTokenResult("access-token", "refresh-token", "bearer", 3600)

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResult:
        self.refresh_token_calls.append(refresh_token)
        return OAuthTokenResult("new-access-token", "rotated-refresh-token", "bearer", 3600)

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider_user_id="00000000-0000-0000-0000-000000000001",
            email="user@example.com",
            email_verified=True,
        )


@pytest.fixture
def fake_cache_service() -> FakeCacheService:
    return FakeCacheService()


@pytest.fixture
def refresh_token_calls() -> list[str]:
    return []


@pytest.fixture
def fake_oauth_provider(refresh_token_calls: list[str]) -> FakeOAuthProvider:
    return FakeOAuthProvider(refresh_token_calls)


@pytest.fixture
def fake_user_repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest_asyncio.fixture
async def client(
    fake_cache_service: FakeCacheService,
    fake_oauth_provider: FakeOAuthProvider,
    fake_user_repository: FakeUserRepository,
) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(
        environment="test",
        database_url="postgresql+asyncpg://unused",
        oauth_redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
        frontend_after_login_url="http://localhost:3000/login",
        session_cookie_secure=False,
    )
    app = create_app(settings, database_check=lambda: True)
    app.dependency_overrides[get_cache_service] = lambda: fake_cache_service
    app.dependency_overrides[get_oauth_provider] = lambda: fake_oauth_provider
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=False,
    ) as test_client:
        yield test_client
