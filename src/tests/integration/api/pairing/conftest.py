"""Fixtures for pairing API integration tests."""

from collections.abc import AsyncIterator
from uuid import UUID

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.screen_pairing_session_repository import (
    SqlAlchemyScreenPairingSessionRepository,
)
from adapters.repositories.user_repository import SqlAlchemyUserRepository
from application.dtos.oauth import OAuthUserInfo
from application.exceptions.authentication import InvalidAccessTokenError
from config.settings import Settings
from domain import User
from drivers.core.app import create_app
from drivers.routers.dependencies import get_oauth_provider, get_user_repository
from drivers.routers.pairing.dependencies import get_screen_pairing_session_repository


class FakeOAuthProvider:
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        if access_token != "valid-access-token":
            raise InvalidAccessTokenError()
        return OAuthUserInfo(
            provider_user_id="00000000-0000-0000-0000-000000000099",
            email="admin@example.com",
            email_verified=True,
        )


@pytest_asyncio.fixture
async def pairing_client(
    integration_session: AsyncSession,
) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(
        environment="test",
        debug=False,
        database_url="postgresql+asyncpg://unused",
    )
    app = create_app(settings)
    repository = SqlAlchemyScreenPairingSessionRepository(integration_session)
    user_repository = SqlAlchemyUserRepository(integration_session)
    await user_repository.save(
        User(id=UUID("00000000-0000-0000-0000-000000000099"))
    )
    app.dependency_overrides[get_screen_pairing_session_repository] = lambda: repository
    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_oauth_provider] = lambda: FakeOAuthProvider()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client
