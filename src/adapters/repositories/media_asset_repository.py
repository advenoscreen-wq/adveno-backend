"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session
from adapters.repositories.mappers import (
    apply_media_asset,
    to_media_asset,
)
from domain.entities.entities import (
    MediaAsset,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    MediaAssetModel,
)


class SqlAlchemyMediaAssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, asset_id: UUID) -> MediaAsset | None:
        model = await self.session.get(MediaAssetModel, asset_id)
        return to_media_asset(model) if model else None

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[MediaAsset]:
        result = await self.session.scalars(
            select(MediaAssetModel).order_by(MediaAssetModel.created_at).offset(offset).limit(limit)
        )
        return [to_media_asset(model) for model in result]

    async def list_active(self, *, offset: int = 0, limit: int = 100) -> list[MediaAsset]:
        result = await self.session.scalars(
            select(MediaAssetModel)
            .where(MediaAssetModel.status == "ACTIVE")
            .order_by(MediaAssetModel.created_at)
            .offset(offset)
            .limit(limit)
        )
        return [to_media_asset(model) for model in result]

    async def save(self, asset: MediaAsset) -> MediaAsset:
        model = MediaAssetModel()
        apply_media_asset(asset, model)
        self.session.add(model)
        await flush_session(self.session, "media asset save")
        return to_media_asset(model)

    async def update(self, asset: MediaAsset) -> MediaAsset:
        model = await self.session.get(MediaAssetModel, asset.id)
        if model is None:
            raise PersistenceError("media asset was not found")
        apply_media_asset(asset, model)
        await flush_session(self.session, "media asset update")
        return to_media_asset(model)
