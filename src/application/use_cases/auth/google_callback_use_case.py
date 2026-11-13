"""Use case for completing Google OAuth sign-in."""

import json
from uuid import UUID

from application.dtos.oauth import OAuthTokenResult
from application.exceptions.oauth import InvalidOAuthStateError, OAuthProviderError
from application.use_cases.auth.commands import GoogleCallbackCommand
from domain import User
from domain.entities.common import utc_now
from ports.repositories.user_repository import UserRepository
from ports.services.cache_service import CacheService
from ports.services.oauth_provider import OAuthProvider


class GoogleCallbackUseCase:
    def __init__(
        self,
        *,
        provider: OAuthProvider,
        cache_service: CacheService,
        user_repository: UserRepository,
    ) -> None:
        self._provider = provider
        self._cache_service = cache_service
        self._user_repository = user_repository

    async def __call__(self, command: GoogleCallbackCommand) -> OAuthTokenResult:
        """Consume the callback state and exchange its code for tokens."""
        stored_attempt = await self._cache_service.pop(f"oauth:state:{command.state}")
        if stored_attempt is None:
            raise InvalidOAuthStateError("OAuth state is invalid or expired")

        try:
            attempt = json.loads(stored_attempt)
        except (json.JSONDecodeError, TypeError) as error:
            raise InvalidOAuthStateError("OAuth state is invalid or expired") from error

        if (
            not isinstance(attempt, dict)
            or attempt.get("state") != command.state
            or attempt.get("redirect_uri") != command.redirect_uri
            or not isinstance(attempt.get("code_verifier"), str)
            or not attempt.get("code_verifier")
        ):
            raise InvalidOAuthStateError("OAuth state is invalid or expired")

        tokens = await self._provider.exchange_code(
            command.code,
            code_verifier=attempt["code_verifier"],
        )
        user_info = await self._provider.get_user_info(tokens.access_token)
        try:
            user_id = UUID(user_info.provider_user_id)
        except (TypeError, ValueError) as error:
            raise OAuthProviderError("OAuth provider returned an invalid user ID") from error

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            await self._user_repository.save(User(id=user_id))
        else:
            user.updated_at = utc_now()
            await self._user_repository.update(user)

        return tokens
