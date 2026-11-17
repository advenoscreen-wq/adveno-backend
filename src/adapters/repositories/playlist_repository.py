"""SQLAlchemy repository implementations for domain persistence contracts."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import flush_session, log_repository_operations
from adapters.repositories.mappers import (
    apply_playlist,
    to_playlist,
    to_playlist_item,
)
from domain.entities.entities import (
    Playlist,
    PlaylistItem,
)
from domain.exceptions import PersistenceError
from drivers.database.models.entities import (
    PlaylistItemModel,
    PlaylistModel,
)


@log_repository_operations
class SqlAlchemyPlaylistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, playlist_id: UUID, *, user_id: UUID | None = None) -> Playlist | None:
        statement = select(PlaylistModel).where(PlaylistModel.id == playlist_id)
        if user_id is not None:
            statement = statement.where(PlaylistModel.user_id == user_id)
        model = await self.session.scalar(statement)
        if model is None:
            return None
        items = await self.session.scalars(
            select(PlaylistItemModel)
            .where(PlaylistItemModel.playlist_id == playlist_id)
            .order_by(PlaylistItemModel.position)
        )
        return to_playlist(model, [to_playlist_item(item) for item in items])

    async def list_all(
        self, *, user_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[Playlist]:
        statement = select(PlaylistModel)
        if user_id is not None:
            statement = statement.where(PlaylistModel.user_id == user_id)
        result = await self.session.scalars(
            statement.order_by(PlaylistModel.created_at).offset(offset).limit(limit)
        )
        return [to_playlist(model) for model in result]

    async def list_by_user_id(
        self,
        user_id: UUID,
        *,
        filter_by_title: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Playlist]:
        statement = select(PlaylistModel).where(PlaylistModel.user_id == user_id)
        if filter_by_title:
            pattern = f"%{filter_by_title}%"
            statement = statement.where(
                or_(PlaylistModel.name.ilike(pattern), PlaylistModel.description.ilike(pattern))
            )
        models = list(
            await self.session.scalars(
                statement.order_by(PlaylistModel.created_at, PlaylistModel.id)
                .offset(offset)
                .limit(limit)
            )
        )
        if not models:
            return []
        items = await self.session.scalars(
            select(PlaylistItemModel)
            .where(PlaylistItemModel.playlist_id.in_([model.id for model in models]))
            .order_by(PlaylistItemModel.playlist_id, PlaylistItemModel.position)
        )
        items_by_playlist: dict[UUID, list[PlaylistItem]] = {model.id: [] for model in models}
        for item in items:
            items_by_playlist[item.playlist_id].append(to_playlist_item(item))
        return [to_playlist(model, items_by_playlist[model.id]) for model in models]

    async def count_by_user_id(self, user_id: UUID, *, filter_by_title: str | None = None) -> int:
        statement = select(func.count(PlaylistModel.id)).where(PlaylistModel.user_id == user_id)
        if filter_by_title:
            pattern = f"%{filter_by_title}%"
            statement = statement.where(
                or_(PlaylistModel.name.ilike(pattern), PlaylistModel.description.ilike(pattern))
            )
        return int(await self.session.scalar(statement) or 0)

    async def save(self, playlist: Playlist) -> Playlist:
        model = PlaylistModel()
        apply_playlist(playlist, model)
        self.session.add(model)
        await flush_session(self.session, "playlist save")
        return to_playlist(model)

    async def update(self, playlist: Playlist) -> Playlist:
        model = await self.session.scalar(
            select(PlaylistModel).where(
                PlaylistModel.id == playlist.id, PlaylistModel.user_id == playlist.user_id
            )
        )
        if model is None:
            raise PersistenceError("playlist was not found")
        apply_playlist(playlist, model)
        await flush_session(self.session, "playlist update")
        return to_playlist(model)

    async def increment_versions(self, playlist_ids: list[UUID]) -> None:
        if not playlist_ids:
            return
        await self.session.execute(
            update(PlaylistModel)
            .where(PlaylistModel.id.in_(playlist_ids))
            .values(
                version=PlaylistModel.version + 1,
                updated_at=func.now(),
            )
        )
        await flush_session(self.session, "playlist version increment")

    async def delete(self, playlist_id: UUID) -> None:
        result = cast(
            CursorResult[Any],
            await self.session.execute(
                delete(PlaylistModel).where(PlaylistModel.id == playlist_id)
            ),
        )
        if result.rowcount == 0:
            raise PersistenceError("playlist was not found")
        await flush_session(self.session, "playlist delete")
