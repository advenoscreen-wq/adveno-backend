"""Dependencies for authentication routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.user_repository import SqlAlchemyUserRepository
from application.use_cases.auth.google_callback_use_case import GoogleCallbackUseCase
from application.use_cases.auth.google_signin_use_case import GoogleSigninUseCase
from application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from drivers.database.database import session_dependency
from drivers.routers.dependencies import CacheService, OAuthProvider, SettingsDependency


def get_google_signin_use_case(
    settings: SettingsDependency,
    cache_service: CacheService,
    provider: OAuthProvider,
) -> GoogleSigninUseCase:
    """Build the Google sign-in use case from its required services."""
    return GoogleSigninUseCase(
        provider=provider,
        cache_service=cache_service,
        state_ttl_seconds=settings.oauth_state_ttl_seconds,
    )


def get_user_repository(
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> SqlAlchemyUserRepository:
    """Build the request-scoped user repository."""
    return SqlAlchemyUserRepository(session)


UserRepositoryDependency = Annotated[
    SqlAlchemyUserRepository,
    Depends(get_user_repository),
]


def get_google_callback_use_case(
    cache_service: CacheService,
    provider: OAuthProvider,
    user_repository: UserRepositoryDependency,
) -> GoogleCallbackUseCase:
    """Build the Google callback use case from its required services."""
    return GoogleCallbackUseCase(
        provider=provider,
        cache_service=cache_service,
        user_repository=user_repository,
    )


def get_refresh_token_use_case(provider: OAuthProvider) -> RefreshTokenUseCase:
    """Build the token refresh use case from the configured provider."""
    return RefreshTokenUseCase(provider=provider)


GoogleSignin = Annotated[
    GoogleSigninUseCase,
    Depends(get_google_signin_use_case),
]
GoogleCallback = Annotated[
    GoogleCallbackUseCase,
    Depends(get_google_callback_use_case),
]
RefreshToken = Annotated[
    RefreshTokenUseCase,
    Depends(get_refresh_token_use_case),
]
