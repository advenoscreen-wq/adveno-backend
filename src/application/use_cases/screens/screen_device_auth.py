"""Shared screen-device credential validation and heartbeat handling."""

import hashlib

from application.exceptions.authentication import InvalidScreenCredentialError
from application.exceptions.screen import ScreenDeviceNotFoundError, ScreenDisconnectedError
from domain import Screen, ScreenCredential
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_repository import ScreenRepository


async def authenticate_screen_device(
    *,
    credential: str,
    screen_repository: ScreenRepository,
    credential_repository: ScreenCredentialRepository,
) -> Screen:
    screen, _ = await authenticate_screen_device_with_credential(
        credential=credential,
        screen_repository=screen_repository,
        credential_repository=credential_repository,
    )
    return screen


async def authenticate_screen_device_with_credential(
    *,
    credential: str,
    screen_repository: ScreenRepository,
    credential_repository: ScreenCredentialRepository,
    persist_credential: bool = True,
) -> tuple[Screen, ScreenCredential]:
    credential_hash = hashlib.sha256(credential.encode("utf-8")).hexdigest()
    device_credential = await credential_repository.get_by_hash(credential_hash)
    if device_credential is None:
        raise ScreenDeviceNotFoundError()

    screen = await screen_repository.get_by_id(device_credential.screen_id)
    if screen is None:
        raise ScreenDeviceNotFoundError()
    if device_credential.revoked_at is not None or not screen.is_active:
        raise ScreenDisconnectedError()
    if not device_credential.is_valid():
        raise InvalidScreenCredentialError()

    device_credential.mark_as_used()
    screen.record_heartbeat()
    if persist_credential:
        await credential_repository.update(device_credential)
    await screen_repository.update(screen)
    return screen, device_credential
