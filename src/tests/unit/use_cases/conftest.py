"""Shared mocks and use-case fixtures for unit tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from application.dtos.oauth import OAuthTokenResult, OAuthUserInfo
from application.use_cases.auth.google_callback_use_case import GoogleCallbackUseCase
from application.use_cases.auth.google_signin_use_case import GoogleSigninUseCase
from application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from application.use_cases.pairing.approve_screen_pairing_session_use_case import (
    ApproveScreenPairingSessionUseCase,
)
from application.use_cases.pairing.create_paired_screen_use_case import (
    CreatePairedScreenUseCase,
)
from application.use_cases.pairing.create_screen_pairing_session_use_case import (
    CreateScreenPairingSessionUseCase,
)
from application.use_cases.pairing.get_screen_pairing_session_status_use_case import (
    GetScreenPairingSessionStatusUseCase,
)
from application.use_cases.pairing.issue_paired_screen_credential_use_case import (
    IssuePairedScreenCredentialUseCase,
)
from application.use_cases.pairing.verify_screen_pairing_session_use_case import (
    VerifyScreenPairingSessionUseCase,
)
from application.use_cases.screens.acknowledge_screen_sync_use_case import (
    AcknowledgeScreenSyncUseCase,
)
from application.use_cases.screens.create_screen_admin_session_use_case import (
    CreateScreenAdminSessionUseCase,
)
from application.use_cases.screens.logout_screen_use_case import LogoutScreenUseCase
from application.use_cases.screens.verify_screen_admin_session_use_case import (
    VerifyScreenAdminSessionUseCase,
)
from application.use_cases.screens.verify_screen_credential_use_case import (
    VerifyScreenCredentialUseCase,
)
from ports.repositories.screen_admin_session_repository import ScreenAdminSessionRepository
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_pairing_session_repository import (
    ScreenPairingSessionRepository,
)
from ports.repositories.screen_repository import ScreenRepository
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository
from ports.repositories.user_repository import UserRepository
from ports.services.cache_service import CacheService
from ports.services.oauth_provider import OAuthProvider
from ports.services.pin_hasher import PinHasher


def _async_port_mock(port: type, *methods: str) -> Mock:
    port_mock = Mock(spec=port)
    for method in methods:
        setattr(port_mock, method, AsyncMock())
    return port_mock


@pytest.fixture
def user_repo() -> Mock:
    repository = _async_port_mock(UserRepository, "get_by_id", "save", "update")
    repository.get_by_id.return_value = None
    repository.save.side_effect = lambda user: user
    repository.update.side_effect = lambda user: user
    return repository


@pytest.fixture
def cache_service() -> Mock:
    return _async_port_mock(
        CacheService,
        "set",
        "get",
        "delete",
        "pop",
        "increment_with_ttl",
    )


@pytest.fixture
def oauth_provider() -> Mock:
    provider = _async_port_mock(
        OAuthProvider,
        "get_authorization_url",
        "exchange_code",
        "refresh_access_token",
        "get_user_info",
    )
    provider.get_authorization_url.return_value = (
        "https://provider.example/authorize?challenge=example"
    )
    provider.exchange_code.return_value = OAuthTokenResult("access", "refresh", "bearer", 3600)
    provider.refresh_access_token.return_value = OAuthTokenResult(
        "new-access", "new-refresh", "bearer", 3600
    )
    provider.get_user_info.return_value = OAuthUserInfo(
        provider_user_id="00000000-0000-0000-0000-000000000001",
        email="user@example.com",
        email_verified=True,
    )
    return provider


@pytest.fixture
def pairing_session_repo() -> Mock:
    repository = _async_port_mock(
        ScreenPairingSessionRepository,
        "get_by_id",
        "get_by_token_hash",
        "get_valid_session",
        "save",
        "update",
    )
    repository.save.side_effect = lambda session: session
    repository.update.side_effect = lambda session: session
    return repository


@pytest.fixture
def screen_repo() -> Mock:
    repository = _async_port_mock(
        ScreenRepository,
        "get_by_id",
        "get_by_screen_code",
        "list_all",
        "list_by_user_id",
        "save",
        "update",
    )
    repository.save.side_effect = lambda screen: screen
    repository.update.side_effect = lambda screen: screen
    return repository


@pytest.fixture
def screen_credential_repo() -> Mock:
    repository = _async_port_mock(
        ScreenCredentialRepository,
        "get_by_hash",
        "get_by_id",
        "get_active_credential_by_screen",
        "get_active_credentials_by_screen",
        "save",
        "update",
    )
    repository.save.side_effect = lambda credential: credential
    repository.update.side_effect = lambda credential: credential
    return repository


@pytest.fixture
def screen_admin_session_repo() -> Mock:
    repository = _async_port_mock(
        ScreenAdminSessionRepository,
        "get_pending_pin_by_screen_id",
        "get_by_screen_id_and_token_hash",
        "save",
        "update",
        "revoke_pending_by_screen_id",
        "revoke_all_for_screen",
    )
    repository.save.side_effect = lambda session: session
    repository.update.side_effect = lambda session: session
    return repository


@pytest.fixture
def pin_hasher() -> Mock:
    hasher = _async_port_mock(PinHasher, "hash_pin", "verify_pin")
    hasher.hash_pin.return_value = "scrypt$mock-hash"
    hasher.verify_pin.return_value = True
    return hasher


@pytest.fixture
def screen_sync_state_repo() -> Mock:
    repository = _async_port_mock(
        ScreenSyncStateRepository,
        "get_by_screen_id",
        "increment_desired_revision",
        "save",
        "update",
    )
    return repository


@pytest.fixture
def google_callback_use_case(
    oauth_provider: Mock,
    cache_service: Mock,
    user_repo: Mock,
) -> GoogleCallbackUseCase:
    return GoogleCallbackUseCase(
        provider=oauth_provider,
        cache_service=cache_service,
        user_repository=user_repo,
    )


@pytest.fixture
def google_signin_use_case(
    oauth_provider: Mock,
    cache_service: Mock,
) -> GoogleSigninUseCase:
    return GoogleSigninUseCase(
        provider=oauth_provider,
        cache_service=cache_service,
        state_ttl_seconds=600,
    )


@pytest.fixture
def refresh_token_use_case(oauth_provider: Mock) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(provider=oauth_provider)


@pytest.fixture
def approve_screen_pairing_session_use_case(
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> ApproveScreenPairingSessionUseCase:
    return ApproveScreenPairingSessionUseCase(
        pairing_session_repository=pairing_session_repo,
        screen_repository=screen_repo,
        screen_credential_repository=screen_credential_repo,
    )


@pytest.fixture
def create_paired_screen_use_case(
    pairing_session_repo: Mock,
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_sync_state_repo: Mock,
) -> CreatePairedScreenUseCase:
    return CreatePairedScreenUseCase(
        pairing_session_repository=pairing_session_repo,
        screen_repository=screen_repo,
        screen_credential_repository=screen_credential_repo,
        screen_sync_state_repository=screen_sync_state_repo,
    )


@pytest.fixture
def create_screen_pairing_session_use_case(
    pairing_session_repo: Mock,
) -> CreateScreenPairingSessionUseCase:
    return CreateScreenPairingSessionUseCase(repository=pairing_session_repo)


@pytest.fixture
def get_screen_pairing_session_status_use_case(
    pairing_session_repo: Mock,
) -> GetScreenPairingSessionStatusUseCase:
    return GetScreenPairingSessionStatusUseCase(repository=pairing_session_repo)


@pytest.fixture
def issue_paired_screen_credential_use_case(
    pairing_session_repo: Mock,
    screen_credential_repo: Mock,
    screen_sync_state_repo: Mock,
) -> IssuePairedScreenCredentialUseCase:
    return IssuePairedScreenCredentialUseCase(
        pairing_session_repository=pairing_session_repo,
        screen_credential_repository=screen_credential_repo,
        screen_sync_state_repository=screen_sync_state_repo,
    )


@pytest.fixture
def verify_screen_pairing_session_use_case(
    pairing_session_repo: Mock,
) -> VerifyScreenPairingSessionUseCase:
    return VerifyScreenPairingSessionUseCase(repository=pairing_session_repo)


@pytest.fixture
def logout_screen_use_case(
    screen_credential_repo: Mock,
    screen_admin_session_repo: Mock,
) -> LogoutScreenUseCase:
    return LogoutScreenUseCase(
        credential_repository=screen_credential_repo,
        admin_session_repository=screen_admin_session_repo,
    )


@pytest.fixture
def create_screen_admin_session_use_case(
    screen_repo: Mock,
    screen_admin_session_repo: Mock,
    pin_hasher: Mock,
) -> CreateScreenAdminSessionUseCase:
    return CreateScreenAdminSessionUseCase(
        screen_repository=screen_repo,
        admin_session_repository=screen_admin_session_repo,
        pin_hasher=pin_hasher,
    )


@pytest.fixture
def verify_screen_admin_session_use_case(
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_admin_session_repo: Mock,
    pin_hasher: Mock,
    cache_service: Mock,
) -> VerifyScreenAdminSessionUseCase:
    cache_service.increment_with_ttl.return_value = 1
    return VerifyScreenAdminSessionUseCase(
        screen_repository=screen_repo,
        credential_repository=screen_credential_repo,
        admin_session_repository=screen_admin_session_repo,
        pin_hasher=pin_hasher,
        cache_service=cache_service,
    )


@pytest.fixture
def acknowledge_screen_sync_use_case(
    screen_repo: Mock,
    screen_credential_repo: Mock,
    screen_sync_state_repo: Mock,
) -> AcknowledgeScreenSyncUseCase:
    return AcknowledgeScreenSyncUseCase(
        screen_repository=screen_repo,
        credential_repository=screen_credential_repo,
        sync_state_repository=screen_sync_state_repo,
    )


@pytest.fixture
def verify_screen_credential_use_case(
    screen_repo: Mock,
    screen_credential_repo: Mock,
) -> VerifyScreenCredentialUseCase:
    return VerifyScreenCredentialUseCase(
        screen_repository=screen_repo,
        credential_repository=screen_credential_repo,
    )
