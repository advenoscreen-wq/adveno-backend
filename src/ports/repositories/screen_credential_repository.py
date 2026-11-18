from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    ScreenCredential,
)


class ScreenCredentialRepository(Protocol):
    async def get_by_id(self, credential_id: UUID) -> ScreenCredential | None: ...

    async def get_by_hash(self, credential_hash: str) -> ScreenCredential | None: ...

    async def get_active_credential_by_screen(
        self, screen_id: UUID, *, for_update: bool = False
    ) -> ScreenCredential | None: ...

    async def get_active_credentials_by_screen(self, screen_id: UUID) -> list[ScreenCredential]: ...

    async def save(self, credential: ScreenCredential) -> ScreenCredential: ...

    async def update(self, credential: ScreenCredential) -> ScreenCredential: ...
