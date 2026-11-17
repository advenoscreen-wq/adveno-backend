from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain import (
    MediaAsset,
)


class MediaAssetRepository(Protocol):
    async def get_by_id(
        self, asset_id: UUID, *, user_id: UUID | None = None
    ) -> MediaAsset | None: ...

    async def list_all(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[MediaAsset]: ...

    async def list_active(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[MediaAsset]: ...

    async def list_by_user_id(
        self,
        user_id: UUID,
        *,
        filter_by_name: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[MediaAsset]: ...

    async def count_by_user_id(
        self, user_id: UUID, *, filter_by_name: str | None = None
    ) -> int: ...

    async def save(self, asset: MediaAsset) -> MediaAsset: ...

    async def update(self, asset: MediaAsset) -> MediaAsset: ...
