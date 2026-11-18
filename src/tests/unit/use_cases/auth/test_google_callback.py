"""Unit tests for the Google OAuth callback use case."""

import json
from unittest.mock import Mock
from uuid import UUID

import pytest

from application.dtos.oauth import OAuthUserInfo
from application.exceptions.oauth import InvalidOAuthStateError, OAuthProviderError
from application.use_cases.auth.commands import GoogleCallbackCommand
from application.use_cases.auth.google_callback_use_case import GoogleCallbackUseCase
from domain import User


@pytest.mark.asyncio
async def test_google_callback_consumes_state_and_exchanges_code(
    google_callback_use_case: GoogleCallbackUseCase,
    cache_service: Mock,
    oauth_provider: Mock,
    user_repo: Mock,
) -> None:
    state = "valid-state"
    redirect_uri = "https://api.example/auth/google/callback"
    code_verifier = "test-verifier"
    cache_service.pop.return_value = json.dumps(
        {
            "state": state,
            "redirect_uri": redirect_uri,
            "created_at": 1,
            "code_verifier": code_verifier,
        }
    )

    result = await google_callback_use_case(
        GoogleCallbackCommand(code="auth-code", state=state, redirect_uri=redirect_uri)
    )

    assert result.refresh_token == "refresh"
    oauth_provider.exchange_code.assert_awaited_once_with("auth-code", code_verifier=code_verifier)
    oauth_provider.get_user_info.assert_awaited_once_with("access")
    user_repo.save.assert_awaited_once()
    saved_user = user_repo.save.await_args.args[0]
    assert saved_user.id == UUID("00000000-0000-0000-0000-000000000001")
    cache_service.pop.assert_awaited_once_with(f"oauth:state:{state}")


@pytest.mark.asyncio
async def test_google_callback_updates_existing_application_user(
    google_callback_use_case: GoogleCallbackUseCase,
    cache_service: Mock,
    user_repo: Mock,
) -> None:
    state = "valid-state"
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    existing_user = User(id=user_id, is_active=False)
    user_repo.get_by_id.return_value = existing_user
    cache_service.pop.return_value = json.dumps(
        {
            "state": state,
            "redirect_uri": "https://api.example/auth/google/callback",
            "code_verifier": "test-verifier",
        }
    )

    await google_callback_use_case(
        GoogleCallbackCommand(
            code="auth-code",
            state=state,
            redirect_uri="https://api.example/auth/google/callback",
        )
    )

    user_repo.update.assert_awaited_once_with(existing_user)
    assert not existing_user.is_active
    user_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_google_callback_rejects_missing_state(
    google_callback_use_case: GoogleCallbackUseCase,
    cache_service: Mock,
    oauth_provider: Mock,
) -> None:
    cache_service.pop.return_value = None
    with pytest.raises(InvalidOAuthStateError):
        await google_callback_use_case(
            GoogleCallbackCommand(
                code="auth-code",
                state="unknown-state",
                redirect_uri="https://api.example/auth/google/callback",
            )
        )

    oauth_provider.exchange_code.assert_not_awaited()


@pytest.mark.asyncio
async def test_google_callback_rejects_replayed_state(
    google_callback_use_case: GoogleCallbackUseCase,
    cache_service: Mock,
    oauth_provider: Mock,
) -> None:
    state = "single-use-state"
    cache_service.pop.side_effect = [
        json.dumps(
            {
                "state": state,
                "redirect_uri": "https://api.example/callback",
                "code_verifier": "verifier",
            }
        ),
        None,
    ]

    command = GoogleCallbackCommand(
        code="auth-code",
        state=state,
        redirect_uri="https://api.example/callback",
    )
    await google_callback_use_case(command)
    with pytest.raises(InvalidOAuthStateError):
        await google_callback_use_case(command)

    oauth_provider.exchange_code.assert_awaited_once_with(
        "auth-code",
        code_verifier="verifier",
    )


@pytest.mark.asyncio
async def test_google_callback_rejects_mismatched_redirect_uri(
    google_callback_use_case: GoogleCallbackUseCase,
    cache_service: Mock,
    oauth_provider: Mock,
) -> None:
    state = "valid-state"
    cache_service.pop.return_value = json.dumps(
        {
            "state": state,
            "redirect_uri": "https://expected.example/callback",
            "code_verifier": "test-verifier",
        }
    )

    with pytest.raises(InvalidOAuthStateError):
        await google_callback_use_case(
            GoogleCallbackCommand(
                code="auth-code",
                state=state,
                redirect_uri="https://other.example/callback",
            )
        )

    oauth_provider.exchange_code.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stored_state",
    [
        "not-json",
        json.dumps(["not", "an", "object"]),
        json.dumps(
            {
                "state": "different-state",
                "redirect_uri": "https://api.example/callback",
                "code_verifier": "verifier",
            }
        ),
        json.dumps(
            {
                "state": "valid-state",
                "redirect_uri": "https://api.example/callback",
                "code_verifier": "",
            }
        ),
    ],
)
async def test_google_callback_rejects_invalid_cached_state_payload(
    google_callback_use_case: GoogleCallbackUseCase,
    cache_service: Mock,
    oauth_provider: Mock,
    stored_state: str,
) -> None:
    cache_service.pop.return_value = stored_state

    with pytest.raises(InvalidOAuthStateError):
        await google_callback_use_case(
            GoogleCallbackCommand(
                code="auth-code",
                state="valid-state",
                redirect_uri="https://api.example/callback",
            )
        )

    oauth_provider.exchange_code.assert_not_awaited()


@pytest.mark.asyncio
async def test_google_callback_rejects_invalid_provider_user_id(
    google_callback_use_case: GoogleCallbackUseCase,
    cache_service: Mock,
    oauth_provider: Mock,
    user_repo: Mock,
) -> None:
    state = "valid-state"
    cache_service.pop.return_value = json.dumps(
        {
            "state": state,
            "redirect_uri": "https://api.example/callback",
            "code_verifier": "verifier",
        }
    )
    oauth_provider.get_user_info.return_value = OAuthUserInfo(
        provider_user_id="invalid-uuid",
        email="user@example.com",
        email_verified=True,
    )

    with pytest.raises(OAuthProviderError, match="invalid user ID"):
        await google_callback_use_case(
            GoogleCallbackCommand(
                code="auth-code",
                state=state,
                redirect_uri="https://api.example/callback",
            )
        )

    user_repo.get_by_id.assert_not_awaited()
    user_repo.save.assert_not_awaited()
    user_repo.update.assert_not_awaited()
