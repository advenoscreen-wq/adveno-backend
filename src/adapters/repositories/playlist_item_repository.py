"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session, log_repository_operations
from adapters.repositories.mappers import (
    apply_playlist_item,
    to_playlist_item,
)
from domain.entities.entities import (
    PlaylistItem,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    MediaAssetModel,
    PlaylistItemModel,
    PlaylistModel,
)


@log_repository_operations
class SqlAlchemyPlaylistItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _validate_ownership(self, item: PlaylistItem) -> None:
        owners = await self.session.execute(
            select(PlaylistModel.user_id, MediaAssetModel.user_id)
            .join(MediaAssetModel, MediaAssetModel.id == item.media_asset_id)
            .where(PlaylistModel.id == item.playlist_id)
        )
        row = owners.one_or_none()
        if row is None:
            raise PersistenceError("playlist or media asset was not found")
        if row[0] != row[1]:
            raise PersistenceError("playlist and media asset belong to different users")

    async def list_by_playlist_id(
        self, playlist_id: UUID, *, offset: int = 0, limit: int = 100
    ) -> list[PlaylistItem]:
        result = await self.session.scalars(
            select(PlaylistItemModel)
            .where(PlaylistItemModel.playlist_id == playlist_id)
            .order_by(PlaylistItemModel.position)
            .offset(offset)
            .limit(limit)
        )
        return [to_playlist_item(model) for model in result]

    async def list_by_media_asset_id(self, media_asset_id: UUID) -> list[PlaylistItem]:
        result = await self.session.scalars(
            select(PlaylistItemModel)
            .where(PlaylistItemModel.media_asset_id == media_asset_id)
            .order_by(PlaylistItemModel.playlist_id)
        )
        return [to_playlist_item(model) for model in result]

    async def delete_by_playlist_id(self, playlist_id: UUID) -> None:
        await self.session.execute(
            delete(PlaylistItemModel).where(PlaylistItemModel.playlist_id == playlist_id)
        )
        await flush_session(self.session, "playlist items delete")

    async def save(self, item: PlaylistItem) -> PlaylistItem:
        await self._validate_ownership(item)
        model = PlaylistItemModel()
        apply_playlist_item(item, model)
        self.session.add(model)
        await flush_session(self.session, "playlist item save")
        return to_playlist_item(model)

    async def update(self, item: PlaylistItem) -> PlaylistItem:
        await self._validate_ownership(item)
        model = await self.session.get(PlaylistItemModel, item.id)
        if model is None:
            raise PersistenceError("playlist item was not found")
        apply_playlist_item(item, model)
        await flush_session(self.session, "playlist item update")
        return to_playlist_item(model)

    async def delete(self, item_id: UUID) -> None:
        result = cast(
            CursorResult[Any],
            await self.session.execute(
                delete(PlaylistItemModel).where(PlaylistItemModel.id == item_id)
            ),
        )
        if result.rowcount == 0:
            raise PersistenceError("playlist item was not found")
        await flush_session(self.session, "playlist item delete")
