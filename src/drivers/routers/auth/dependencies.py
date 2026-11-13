"""Dependencies for authentication routes."""

from typing import Annotated

from fastapi import Depends

from application.use_cases.auth.google_signin_use_case import GoogleSigninUseCase
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


GoogleSignin = Annotated[
    GoogleSigninUseCase,
    Depends(get_google_signin_use_case),
]
