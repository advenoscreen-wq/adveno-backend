"""Unit tests for the refresh-token use case."""

from unittest.mock import Mock

import pytest

from application.dtos.oauth import OAuthTokenResult
from application.exceptions.oauth import OAuthProviderError
from application.use_cases.auth.commands import RefreshTokenCommand
from application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase


@pytest.mark.asyncio
async def test_refresh_token_returns_rotated_tokens(
    refresh_token_use_case: RefreshTokenUseCase,
    oauth_provider: Mock,
) -> None:
    result = await refresh_token_use_case(RefreshTokenCommand("old-refresh-token"))

    assert result == OAuthTokenResult("new-access", "new-refresh", "bearer", 3600)
    oauth_provider.refresh_access_token.assert_awaited_once_with("old-refresh-token")


@pytest.mark.asyncio
async def test_refresh_token_requires_a_new_refresh_token(
    refresh_token_use_case: RefreshTokenUseCase,
    oauth_provider: Mock,
) -> None:
    oauth_provider.refresh_access_token.return_value = OAuthTokenResult(
        "new-access", None, "bearer", 3600
    )

    with pytest.raises(OAuthProviderError, match="did not return a refresh token"):
        await refresh_token_use_case(RefreshTokenCommand("old-refresh-token"))
