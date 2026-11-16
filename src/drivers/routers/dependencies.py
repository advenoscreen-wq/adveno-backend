"""Dependencies shared by multiple HTTP route groups."""

from functools import lru_cache
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adapters.repositories.user_repository import SqlAlchemyUserRepository
from adapters.services.oauth_service.supabase_oauth import SupabaseOAuthAdapter
from adapters.services.redis_cache_service import RedisCacheService
from application.exceptions.authentication import (
    AuthenticationRequiredError,
    InvalidAccessTokenError,
)
from config.settings import Settings, get_settings
from domain import User
from drivers.database.database import check_database, session_dependency


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """Return the database factory configured by the application."""
    return cast(async_sessionmaker[AsyncSession], request.app.state.session_factory)


@lru_cache(maxsize=8)
def _cache_service(redis_url: str) -> RedisCacheService:
    return RedisCacheService(redis_url)


def get_cache_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedisCacheService:
    """Return the process-wide cache adapter for the configured Redis URL."""
    return _cache_service(settings.redis_url)


@lru_cache(maxsize=8)
def _oauth_provider(url: str, anon_key: str, provider: str) -> SupabaseOAuthAdapter:
    return SupabaseOAuthAdapter(
        supabase_url=url,
        supabase_anon_key=anon_key,
        provider=provider,
    )


def get_oauth_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SupabaseOAuthAdapter:
    """Return the configured OAuth provider adapter."""
    return _oauth_provider(
        settings.supabase_url,
        settings.supabase_anon_key.get_secret_value(),
        settings.oauth_provider,
    )


async def get_database_ready(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> bool:
    """Check database connectivity for readiness probes."""
    return await check_database(session_factory)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> SqlAlchemyUserRepository:
    """Build the request-scoped user repository."""
    return SqlAlchemyUserRepository(session)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(HTTPBearer(auto_error=False)),
    ],
    provider: Annotated[SupabaseOAuthAdapter, Depends(get_oauth_provider)],
    user_repository: Annotated[
        SqlAlchemyUserRepository,
        Depends(get_user_repository),
    ],
) -> User:
    """Validate the bearer token and return its active application user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationRequiredError()

    try:
        identity = await provider.get_user_info(credentials.credentials)
    except InvalidAccessTokenError as error:
        raise AuthenticationRequiredError() from error

    try:
        user_id = UUID(identity.provider_user_id)
    except (TypeError, ValueError) as error:
        raise AuthenticationRequiredError() from error

    user = await user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationRequiredError()
    return user


async def get_authenticated_access_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(HTTPBearer(auto_error=False)),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> str:
    """Return the bearer token after validating the active application user."""
    if credentials is None:
        raise AuthenticationRequiredError()
    return credentials.credentials


SettingsDependency = Annotated[Settings, Depends(get_settings)]
CacheService = Annotated[RedisCacheService, Depends(get_cache_service)]
OAuthProvider = Annotated[SupabaseOAuthAdapter, Depends(get_oauth_provider)]
DatabaseReady = Annotated[bool, Depends(get_database_ready)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AuthenticatedAccessToken = Annotated[str, Depends(get_authenticated_access_token)]
