"""List a user's playlists with title and description filtering."""

from math import ceil
from uuid import UUID

from application.use_cases.playlists.results import ListPlaylistsResult
from ports.repositories.playlist_repository import PlaylistRepository


class ListPlaylistsUseCase:
    def __init__(self, *, playlist_repository: PlaylistRepository) -> None:
        self._playlist_repository = playlist_repository

    async def __call__(
        self,
        *,
        user_id: UUID,
        filter_by_title: str | None,
        page: int,
        limit: int,
    ) -> ListPlaylistsResult:
        title_filter = filter_by_title.strip() if filter_by_title else None
        title_filter = title_filter or None
        total_items = await self._playlist_repository.count_by_user_id(
            user_id,
            filter_by_title=title_filter,
        )
        total_pages = ceil(total_items / limit) if total_items else 0
        items = await self._playlist_repository.list_by_user_id(
            user_id,
            filter_by_title=title_filter,
            offset=(page - 1) * limit,
            limit=limit,
        )
        return ListPlaylistsResult(
            items=items,
            total_pages=total_pages,
            total_items=total_items,
            has_next=page < total_pages,
            has_prev=page > 1,
            limit=limit,
            page=page,
        )
