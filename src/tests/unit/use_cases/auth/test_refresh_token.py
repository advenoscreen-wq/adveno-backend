"""Unit tests for the refresh-token use case."""

from typing import Any

import pytest

from application.dtos.oauth import OAuthTokenResult
from application.exceptions.oauth import OAuthProviderError
from application.use_cases.auth.commands import RefreshTokenCommand
from application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase


@pytest.mark.asyncio
async def test_refresh_token_returns_rotated_tokens(
    refresh_token_use_case: RefreshTokenUseCase,
    fake_oauth_provider: Any,
) -> None:
    result = await refresh_token_use_case(RefreshTokenCommand("old-refresh-token"))

    assert result == OAuthTokenResult(
        "new-access", "new-refresh", "bearer", 3600
    )
    assert fake_oauth_provider.refreshed == ["old-refresh-token"]


@pytest.mark.asyncio
async def test_refresh_token_requires_a_new_refresh_token(
    refresh_token_use_case: RefreshTokenUseCase,
    fake_oauth_provider: Any,
) -> None:
    fake_oauth_provider.refresh_result = OAuthTokenResult(
        "new-access", None, "bearer", 3600
    )

    with pytest.raises(OAuthProviderError, match="did not return a refresh token"):
        await refresh_token_use_case(RefreshTokenCommand("old-refresh-token"))
