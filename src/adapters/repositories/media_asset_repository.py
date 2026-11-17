"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session, log_repository_operations
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


@log_repository_operations
class SqlAlchemyMediaAssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, asset_id: UUID, *, user_id: UUID | None = None) -> MediaAsset | None:
        statement = select(MediaAssetModel).where(MediaAssetModel.id == asset_id)
        if user_id is not None:
            statement = statement.where(MediaAssetModel.user_id == user_id)
        model = await self.session.scalar(statement)
        return to_media_asset(model) if model else None

    async def list_all(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[MediaAsset]:
        statement = select(MediaAssetModel)
        if user_id is not None:
            statement = statement.where(MediaAssetModel.user_id == user_id)
        result = await self.session.scalars(
            statement.order_by(MediaAssetModel.created_at).offset(offset).limit(limit)
        )
        return [to_media_asset(model) for model in result]

    async def list_active(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[MediaAsset]:
        statement = select(MediaAssetModel).where(MediaAssetModel.status == "ACTIVE")
        if user_id is not None:
            statement = statement.where(MediaAssetModel.user_id == user_id)
        result = await self.session.scalars(
            statement.order_by(MediaAssetModel.created_at).offset(offset).limit(limit)
        )
        return [to_media_asset(model) for model in result]

    async def list_by_user_id(
        self, user_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[MediaAsset]:
        return await self.list_all(user_id=user_id, offset=offset, limit=limit)

    async def save(self, asset: MediaAsset) -> MediaAsset:
        model = MediaAssetModel()
        apply_media_asset(asset, model)
        self.session.add(model)
        await flush_session(self.session, "media asset save")
        return to_media_asset(model)

    async def update(self, asset: MediaAsset) -> MediaAsset:
        model = await self.session.scalar(
            select(MediaAssetModel).where(
                MediaAssetModel.id == asset.id, MediaAssetModel.user_id == asset.user_id
            )
        )
        if model is None:
            raise PersistenceError("media asset was not found")
        apply_media_asset(asset, model)
        await flush_session(self.session, "media asset update")
        return to_media_asset(model)
