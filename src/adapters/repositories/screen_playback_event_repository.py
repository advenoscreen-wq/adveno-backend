"""SQLAlchemy repository for immutable screen playback events."""

from collections.abc import Sequence

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.common import log_repository_operations
from domain import ScreenPlaybackEvent
from drivers.database.models.screen_playback_event import ScreenPlaybackEventModel


@log_repository_operations
class SqlAlchemyScreenPlaybackEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_many_idempotently(self, events: Sequence[ScreenPlaybackEvent]) -> int:
        if not events:
            return 0
        statement = (
            insert(ScreenPlaybackEventModel)
            .values(
                [
                    {
                        "id": event.id,
                        "event_id": event.event_id,
                        "screen_id": event.screen_id,
                        "playlist_id": event.playlist_id,
                        "playlist_item_id": event.playlist_item_id,
                        "media_asset_id": event.media_asset_id,
                        "playlist_version": event.playlist_version,
                        "media_checksum": event.media_checksum,
                        "played_at": event.played_at,
                        "played_complete_at": event.played_complete_at,
                    }
                    for event in events
                ]
            )
            .on_conflict_do_nothing(constraint="uq_playback_events_screen_event_id")
            .returning(ScreenPlaybackEventModel.id)
        )
        result = await self.session.scalars(statement)
        return len(result.all())
