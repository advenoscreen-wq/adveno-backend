"""List a user's screens with pagination."""

from math import ceil
from uuid import UUID

from application.use_cases.screens.results import ListScreensResult
from ports.repositories.screen_repository import ScreenRepository


class ListScreensUseCase:
    def __init__(self, *, screen_repository: ScreenRepository) -> None:
        self._screen_repository = screen_repository

    async def __call__(
        self,
        *,
        user_id: UUID,
        filter_by_name: str | None,
        page: int,
        limit: int,
    ) -> ListScreensResult:
        name_filter = filter_by_name.strip() if filter_by_name else None
        name_filter = name_filter or None
        total_items = await self._screen_repository.count_by_user_id(
            user_id,
            filter_by_name=name_filter,
        )
        total_pages = ceil(total_items / limit) if total_items else 0
        items = await self._screen_repository.list_by_user_id(
            user_id,
            filter_by_name=name_filter,
            offset=(page - 1) * limit,
            limit=limit,
        )
        return ListScreensResult(
            items=items,
            total_pages=total_pages,
            total_items=total_items,
            has_next=page < total_pages,
            has_prev=page > 1,
            limit=limit,
            page=page,
        )
