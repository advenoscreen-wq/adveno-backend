"""Google OAuth request routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from application.exceptions.oauth import (
    InvalidOAuthStateError,
    OAuthCallbackError,
    OAuthProviderError,
)
from application.use_cases.auth.commands import GoogleCallbackCommand, GoogleSigninCommand
from drivers.routers.auth.dependencies import GoogleCallback, GoogleSignin
from drivers.routers.dependencies import SettingsDependency

router = APIRouter(tags=["authentication"])

CALLBACK_FRAGMENT_BRIDGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Completing sign-in</title></head>
<body><p id="message">Completing sign-in…</p><script>
const fragment = new URLSearchParams(window.location.hash.slice(1));
const oauthError = fragment.get("error");
window.history.replaceState(
  null,
  "",
  window.location.pathname + window.location.search
);
if (oauthError) {
  const query = new URLSearchParams(window.location.search);
  for (const key of ["error", "error_code", "error_description"]) {
    const value = fragment.get(key);
    if (value) query.set(key, value);
  }
  window.location.replace(window.location.pathname + "?" + query.toString());
} else {
  document.getElementById("message").textContent =
    "No authorization code was returned. Please start sign-in again.";
}
</script></body></html>"""


@router.get("/google/request")
async def google_signin_request(
    settings: SettingsDependency,
    google_signin: GoogleSignin,
) -> RedirectResponse:
    result = await google_signin(GoogleSigninCommand(settings.oauth_redirect_uri))
    response = RedirectResponse(result.authorization_url, status_code=307)
    response.set_cookie(
        key=settings.oauth_state_cookie_name,
        value=result.state,
        max_age=settings.oauth_state_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/api/v1/auth/google/callback",
    )
    return response


@router.get("/google/callback")
async def google_signin_callback(
    request: Request,
    settings: SettingsDependency,
    google_callback: GoogleCallback,
    code: str | None = None,
    error: str | None = None,
    error_code: str | None = None,
    error_description: str | None = None,
) -> Response:
    if error is not None:
        raise OAuthCallbackError(error, error_code)
    if not code:
        return HTMLResponse(
            CALLBACK_FRAGMENT_BRIDGE,
            headers={
                "Cache-Control": "no-store",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": (
                    "default-src 'none'; script-src 'unsafe-inline'; "
                    "base-uri 'none'; frame-ancestors 'none'"
                ),
            },
        )

    state = request.cookies.get(settings.oauth_state_cookie_name)
    if not state:
        raise InvalidOAuthStateError()
    tokens = await google_callback(
        GoogleCallbackCommand(
            code=code,
            state=state,
            redirect_uri=settings.oauth_redirect_uri,
        )
    )

    if not tokens.refresh_token:
        raise OAuthProviderError("OAuth provider did not return a refresh token")
    response = RedirectResponse(settings.frontend_after_login_url, status_code=303)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=tokens.refresh_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(
        key=settings.oauth_state_cookie_name,
        path="/api/v1/auth/google/callback",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return response
