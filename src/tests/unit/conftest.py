"""Unit-test fixtures."""

import pytest

from application.use_cases.auth.google_signin_use_case import GoogleSigninUseCase


class FakeOAuthProvider:
    async def get_authorization_url(
        self,
        *,
        redirect_uri: str,
        state: str,
        scopes: list[str] | None = None,
    ) -> str:
        return f"https://provider.example/authorize?state={state}&redirect={redirect_uri}"


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


@pytest.fixture
def google_signin_use_case() -> GoogleSigninUseCase:
    """Build the Google sign-in request use case for unit tests."""
    return GoogleSigninUseCase(
        provider=FakeOAuthProvider(),
        cache_service=FakeCacheService(),
        state_ttl_seconds=600,
    )
