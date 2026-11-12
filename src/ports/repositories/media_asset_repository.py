from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    MediaAsset,
)


class MediaAssetRepository(Protocol):
    async def get_by_id(self, asset_id: UUID) -> MediaAsset | None: ...

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[MediaAsset]: ...

    async def list_active(self, *, offset: int = 0, limit: int = 100) -> list[MediaAsset]: ...

    async def save(self, asset: MediaAsset) -> MediaAsset: ...

    async def update(self, asset: MediaAsset) -> MediaAsset: ...
