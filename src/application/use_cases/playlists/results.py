"""Results returned by playlist use cases."""

from dataclasses import dataclass

from domain import Playlist


@dataclass(frozen=True)
class ListPlaylistsResult:
    items: list[Playlist]
    total_pages: int
    total_items: int
    has_next: bool
    has_prev: bool
    limit: int
    page: int
