"""Unit tests for the Google OAuth callback use case."""

import json
from typing import Any
from uuid import UUID

import pytest

from application.exceptions.oauth import InvalidOAuthStateError
from application.use_cases.auth.commands import GoogleCallbackCommand
from application.use_cases.auth.google_callback_use_case import GoogleCallbackUseCase
from domain import User


@pytest.mark.asyncio
async def test_google_callback_consumes_state_and_exchanges_code(
    google_callback_use_case: GoogleCallbackUseCase,
    fake_cache_service: Any,
    fake_oauth_provider: Any,
    fake_user_repository: Any,
) -> None:
    state = "valid-state"
    redirect_uri = "https://api.example/auth/google/callback"
    code_verifier = "test-verifier"
    fake_cache_service.values[f"oauth:state:{state}"] = json.dumps(
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
    assert fake_oauth_provider.exchanged == ("auth-code", code_verifier)
    assert len(fake_user_repository.saved) == 1
    assert fake_user_repository.saved[0].id == UUID("00000000-0000-0000-0000-000000000001")
    assert await fake_cache_service.get(f"oauth:state:{state}") is None


@pytest.mark.asyncio
async def test_google_callback_updates_existing_application_user(
    google_callback_use_case: GoogleCallbackUseCase,
    fake_cache_service: Any,
    fake_user_repository: Any,
) -> None:
    state = "valid-state"
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    existing_user = User(id=user_id, is_active=False)
    fake_user_repository.users[user_id] = existing_user
    fake_cache_service.values[f"oauth:state:{state}"] = json.dumps(
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

    assert fake_user_repository.updated == [existing_user]
    assert not existing_user.is_active
    assert fake_user_repository.saved == []


@pytest.mark.asyncio
async def test_google_callback_rejects_missing_or_replayed_state(
    google_callback_use_case: GoogleCallbackUseCase,
    fake_oauth_provider: Any,
) -> None:
    with pytest.raises(InvalidOAuthStateError):
        await google_callback_use_case(
            GoogleCallbackCommand(
                code="auth-code",
                state="unknown-state",
                redirect_uri="https://api.example/auth/google/callback",
            )
        )

    assert fake_oauth_provider.exchanged is None


@pytest.mark.asyncio
async def test_google_callback_rejects_mismatched_redirect_uri(
    google_callback_use_case: GoogleCallbackUseCase,
    fake_cache_service: Any,
    fake_oauth_provider: Any,
) -> None:
    state = "valid-state"
    fake_cache_service.values[f"oauth:state:{state}"] = json.dumps(
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

    assert fake_oauth_provider.exchanged is None
