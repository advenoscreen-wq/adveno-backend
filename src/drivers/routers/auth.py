"""BFF OAuth authentication endpoints."""

from __future__ import annotations

from typing import Annotated

from application.auth.oauth_service import BFFAuthenticationService
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.user_repository import SqlAlchemyUserRepository
from application.exceptions.oauth import OAuthProviderError
from config.settings import Settings
from drivers.database.database import session_dependency

router = APIRouter(prefix="/auth", tags=["authentication"])
DatabaseSession = Annotated[AsyncSession, Depends(session_dependency)]


def _service(request: Request, session: AsyncSession) -> BFFAuthenticationService:
    settings: Settings = request.app.state.settings
    return BFFAuthenticationService(
        provider=request.app.state.oauth_provider,
        user_repository=SqlAlchemyUserRepository(session),
        cache_service=request.app.state.cache_service,
        session_secret=settings.jwt_secret.get_secret_value(),
        state_ttl_seconds=settings.oauth_state_ttl_seconds,
        session_ttl_seconds=settings.session_ttl_seconds,
    )


@router.get("/oauth/login", include_in_schema=False)
async def oauth_login(request: Request) -> RedirectResponse:
    settings: Settings = request.app.state.settings
    if not settings.supabase_url or not settings.supabase_anon_key.get_secret_value():
        raise HTTPException(status_code=503, detail="OAuth is not configured")
    service = _service(request, request.state.db_session)
    authorization_url = await service.begin_login(settings.oauth_redirect_uri)
    return RedirectResponse(authorization_url, status_code=307)


@router.get("/oauth/callback", include_in_schema=False)
async def oauth_callback(
    request: Request,
    code: str,
    state: str,
    session: DatabaseSession,
) -> RedirectResponse:
    settings: Settings = request.app.state.settings
    try:
        application_session = await _service(request, session).complete_login(
            code=code, state=state
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OAuthProviderError as error:
        raise HTTPException(status_code=502, detail="OAuth provider request failed") from error
    response = RedirectResponse(settings.frontend_after_login_url, status_code=303)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=application_session,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return response
