"""Authentication session routes."""

from fastapi import APIRouter

from application.exceptions.oauth import OAuthProviderError
from application.use_cases.auth.commands import RefreshTokenCommand
from drivers.routers.auth.dependencies import RefreshToken
from drivers.schemas.auth import RefreshTokenRequest, RefreshTokenResponse

router = APIRouter(tags=["authentication"])


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_session(
    body: RefreshTokenRequest,
    refresh_token: RefreshToken,
) -> RefreshTokenResponse:
    tokens = await refresh_token(
        RefreshTokenCommand(refresh_token=body.refresh_token.get_secret_value())
    )
    rotated_refresh_token = tokens.refresh_token
    if not rotated_refresh_token:
        raise OAuthProviderError("OAuth provider did not return a refresh token")
    return RefreshTokenResponse(
        access_token=tokens.access_token,
        refresh_token=rotated_refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )
