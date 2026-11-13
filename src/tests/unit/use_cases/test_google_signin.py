"""Unit tests for the Google sign-in request use case."""

from application.use_cases.auth.commands import GoogleSigninCommand
from application.use_cases.auth.results import GoogleSigninResult
from application.use_cases.auth.google_signin_use_case import GoogleSigninUseCase


async def test_google_signin_use_case_returns_authorization_url(
    google_signin_use_case: GoogleSigninUseCase,
) -> None:
    result = await google_signin_use_case(
        GoogleSigninCommand("http://localhost:8000/api/v1/auth/oauth/callback")
    )

    assert isinstance(result, GoogleSigninResult)
    assert result.authorization_url.startswith("https://provider.example/authorize?")
