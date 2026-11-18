"""Unit tests for the Google sign-in request use case."""

import base64
import hashlib
import json
from unittest.mock import Mock

from application.use_cases.auth.commands import GoogleSigninCommand
from application.use_cases.auth.google_signin_use_case import GoogleSigninUseCase
from application.use_cases.auth.results import GoogleSigninResult


async def test_google_signin_use_case_returns_authorization_url(
    google_signin_use_case: GoogleSigninUseCase,
    oauth_provider: Mock,
    cache_service: Mock,
) -> None:
    redirect_uri = "http://localhost:8000/api/v1/auth/oauth/callback"
    result = await google_signin_use_case(GoogleSigninCommand(redirect_uri))

    assert isinstance(result, GoogleSigninResult)
    assert result.authorization_url.startswith("https://provider.example/authorize?")
    oauth_provider.get_authorization_url.assert_awaited_once()
    provider_args = oauth_provider.get_authorization_url.await_args.kwargs
    assert provider_args["redirect_uri"] == redirect_uri

    cache_service.set.assert_awaited_once()
    cache_key, serialized_attempt = cache_service.set.await_args.args
    saved_attempt = json.loads(serialized_attempt)
    assert cache_key == f"oauth:state:{result.state}"
    assert saved_attempt["state"] == result.state
    assert saved_attempt["redirect_uri"] == redirect_uri
    expected_challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(saved_attempt["code_verifier"].encode("ascii")).digest()
        )
        .rstrip(b"=")
        .decode("ascii")
    )
    assert provider_args["code_challenge"] == expected_challenge
    assert cache_service.set.await_args.kwargs["ttl_seconds"] == 600
