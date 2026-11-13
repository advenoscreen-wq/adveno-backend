"""Dependencies shared by multiple HTTP route groups."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adapters.services.oauth_service.supabase_oauth import SupabaseOAuthAdapter
from adapters.services.redis_cache_service import RedisCacheService
from config.settings import Settings, get_settings
from drivers.database.database import check_database


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """Return the database factory configured by the application."""
    return request.app.state.session_factory


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
    session_factory: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_factory)
    ],
) -> bool:
    """Check database connectivity for readiness probes."""
    return await check_database(session_factory)


SettingsDependency = Annotated[Settings, Depends(get_settings)]
CacheService = Annotated[RedisCacheService, Depends(get_cache_service)]
OAuthProvider = Annotated[SupabaseOAuthAdapter, Depends(get_oauth_provider)]
DatabaseReady = Annotated[bool, Depends(get_database_ready)]
