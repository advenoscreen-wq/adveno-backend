"""Results returned by screen use cases."""

from dataclasses import dataclass

from domain import Playlist, Screen


@dataclass(frozen=True)
class GetScreenResult:
    screen: Screen
    assigned_playlist: Playlist | None


@dataclass(frozen=True)
class ListScreensResult:
    items: list[Screen]
    total_pages: int
    total_items: int
    has_next: bool
    has_prev: bool
    limit: int
    page: int
