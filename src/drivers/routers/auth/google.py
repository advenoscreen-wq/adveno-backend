"""Google OAuth request routes."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from application.use_cases.auth.commands import GoogleSigninCommand
from drivers.routers.auth.dependencies import GoogleSignin
from drivers.routers.dependencies import SettingsDependency

router = APIRouter(tags=["authentication"])


@router.get("/google/request")
async def google_signin_request(
    settings: SettingsDependency,
    google_signin: GoogleSignin,
) -> RedirectResponse:
    result = await google_signin(GoogleSigninCommand(settings.oauth_redirect_uri))
    return RedirectResponse(result.authorization_url, status_code=307)
