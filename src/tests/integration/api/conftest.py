"""Shared API integration client backed by Postgres and Redis containers."""

from collections.abc import AsyncIterator
from typing import Annotated
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import httpx
import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer

from adapters.repositories.user_repository import SqlAlchemyUserRepository
from adapters.services.redis_cache_service import RedisCacheService
from application.dtos.oauth import OAuthTokenResult, OAuthUserInfo
from application.exceptions.authentication import (
    AuthenticationRequiredError,
    InvalidAccessTokenError,
)
from config.settings import Settings
from domain import User
from drivers.core.app import create_app
from drivers.routers.dependencies import (
    get_access_token_user_id,
    get_cache_service,
    get_oauth_provider,
)
from drivers.routers.media.dependencies import get_storage_service
from ports.services.oauth_provider import OAuthProvider
from ports.services.storage_service import StorageService

ADMIN_ID = UUID("00000000-0000-0000-0000-000000000099")
CALLBACK_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def oauth_provider() -> Mock:
    """Mock the external OAuth provider while retaining realistic responses."""
    provider = Mock(spec=OAuthProvider)
    provider.get_authorization_url = AsyncMock(
        return_value="https://provider.example/authorize?code_challenge=challenge"
        "&code_challenge_method=s256"
    )
    provider.exchange_code = AsyncMock(
        return_value=OAuthTokenResult("access-token", "refresh-token", "bearer", 3600)
    )
    provider.refresh_access_token = AsyncMock(
        return_value=OAuthTokenResult("new-access-token", "rotated-refresh-token", "bearer", 3600)
    )

    async def get_user_info(access_token: str) -> OAuthUserInfo:
        if access_token == "invalid-access-token":
            raise InvalidAccessTokenError()
        user_id = ADMIN_ID if access_token == "valid-access-token" else CALLBACK_USER_ID
        return OAuthUserInfo(
            provider_user_id=str(user_id),
            email="user@example.com",
            email_verified=True,
        )

    provider.get_user_info = AsyncMock(side_effect=get_user_info)
    return provider


@pytest.fixture
def storage_service() -> Mock:
    """Mock object storage while keeping API tests isolated from Supabase."""
    service = Mock(spec=StorageService)
    service.create_signed_upload_url = AsyncMock(
        return_value="https://storage.example/signed-upload"
    )
    service.get_public_url = Mock(
        side_effect=lambda *, bucket, object_path: (
            f"https://project.supabase.co/storage/v1/object/public/{bucket}/{object_path}"
        )
    )
    return service


@pytest_asyncio.fixture
async def api_app(
    postgres_container: PostgresContainer,
    redis_container: RedisContainer,
    redis_service: RedisCacheService,
    integration_session: AsyncSession,
    oauth_provider: Mock,
    storage_service: Mock,
) -> AsyncIterator[FastAPI]:
    """Create the application using real test databases and mocked OAuth API."""
    database_url = postgres_container.get_connection_url().replace(
        "postgresql+psycopg2://",
        "postgresql+asyncpg://",
    )
    redis_url = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
    settings = Settings(
        environment="test",
        debug=False,
        database_url=database_url,
        redis_url=redis_url,
        supabase_url="https://project.supabase.co",
        media_storage_bucket="media",
        oauth_redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
        frontend_after_login_url="http://localhost:3000/login",
        session_cookie_secure=False,
    )
    await integration_session.execute(
        text("INSERT INTO auth.users (id) VALUES (:id), (:admin_id) ON CONFLICT DO NOTHING"),
        {"id": CALLBACK_USER_ID, "admin_id": ADMIN_ID},
    )
    await SqlAlchemyUserRepository(integration_session).save(User(id=ADMIN_ID))
    await integration_session.commit()

    app = create_app(settings)
    app.dependency_overrides[get_cache_service] = lambda: redis_service
    app.dependency_overrides[get_oauth_provider] = lambda: oauth_provider

    async def test_access_token_user_id(
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(HTTPBearer(auto_error=False)),
        ],
    ) -> UUID:
        if credentials is None or credentials.credentials != "valid-access-token":
            raise AuthenticationRequiredError()
        return ADMIN_ID

    app.dependency_overrides[get_access_token_user_id] = test_access_token_user_id
    app.dependency_overrides[get_storage_service] = lambda: storage_service
    try:
        yield app
    finally:
        await app.state.session_factory.kw["bind"].dispose()


@pytest_asyncio.fixture
async def client(api_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Create an async client for the shared integration application."""
    transport = httpx.ASGITransport(app=api_app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=False,
    ) as test_client:
        yield test_client
