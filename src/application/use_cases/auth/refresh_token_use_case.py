"""Use case for refreshing a Supabase Auth session."""

from application.dtos.oauth import OAuthTokenResult
from application.exceptions.oauth import OAuthProviderError
from application.use_cases.auth.commands import RefreshTokenCommand
from ports.services.oauth_provider import OAuthProvider


class RefreshTokenUseCase:
    def __init__(self, *, provider: OAuthProvider) -> None:
        self._provider = provider

    async def __call__(self, command: RefreshTokenCommand) -> OAuthTokenResult:
        """Exchange a refresh token for the current access and refresh tokens."""
        result = await self._provider.refresh_access_token(command.refresh_token)
        if not result.refresh_token:
            raise OAuthProviderError("OAuth provider did not return a refresh token")
        return result
