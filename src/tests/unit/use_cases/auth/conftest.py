"""Fixtures for authentication use-case tests."""

from uuid import UUID

import pytest

from application.dtos.oauth import OAuthTokenResult, OAuthUserInfo
from application.use_cases.auth.google_callback_use_case import GoogleCallbackUseCase
from application.use_cases.auth.google_signin_use_case import GoogleSigninUseCase
from application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from domain import User


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
    def __init__(self) -> None:
        self.exchanged: tuple[str, str] | None = None
        self.refreshed: list[str] = []
        self.refresh_result = OAuthTokenResult(
            "new-access", "new-refresh", "bearer", 3600
        )

    async def get_authorization_url(
        self,
        *,
        redirect_uri: str,
        code_challenge: str | None = None,
        scopes: list[str] | None = None,
    ) -> str:
        return (
            "https://provider.example/authorize?"
            f"challenge={code_challenge}&redirect={redirect_uri}"
        )

    async def exchange_code(self, code: str, *, code_verifier: str) -> OAuthTokenResult:
        self.exchanged = (code, code_verifier)
        return OAuthTokenResult("access", "refresh", "bearer", 3600)

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResult:
        self.refreshed.append(refresh_token)
        return self.refresh_result

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider_user_id="00000000-0000-0000-0000-000000000001",
            email="user@example.com",
            email_verified=True,
        )


@pytest.fixture
def fake_user_repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def fake_cache_service() -> FakeCacheService:
    return FakeCacheService()


@pytest.fixture
def fake_oauth_provider() -> FakeOAuthProvider:
    return FakeOAuthProvider()


@pytest.fixture
def google_callback_use_case(
    fake_oauth_provider: FakeOAuthProvider,
    fake_cache_service: FakeCacheService,
    fake_user_repository: FakeUserRepository,
) -> GoogleCallbackUseCase:
    return GoogleCallbackUseCase(
        provider=fake_oauth_provider,
        cache_service=fake_cache_service,
        user_repository=fake_user_repository,
    )


@pytest.fixture
def google_signin_use_case(
    fake_oauth_provider: FakeOAuthProvider,
    fake_cache_service: FakeCacheService,
) -> GoogleSigninUseCase:
    return GoogleSigninUseCase(
        provider=fake_oauth_provider,
        cache_service=fake_cache_service,
        state_ttl_seconds=600,
    )


@pytest.fixture
def refresh_token_use_case(fake_oauth_provider: FakeOAuthProvider) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(provider=fake_oauth_provider)
