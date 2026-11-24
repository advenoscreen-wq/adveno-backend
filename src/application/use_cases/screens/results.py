"""Results returned by screen use cases."""

from dataclasses import dataclass

from domain import MediaAsset, Playlist, PlaylistItem, Screen


@dataclass(frozen=True)
class PlaylistMediaWithUrl:
    media: MediaAsset
    media_url: str


@dataclass(frozen=True)
class AssignedPlaylistItem:
    item: PlaylistItem
    media: PlaylistMediaWithUrl


@dataclass(frozen=True)
class AssignedPlaylistResult:
    playlist: Playlist | None
    items: list[AssignedPlaylistItem]


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


@dataclass(frozen=True)
class ScreenSyncCheckResult:
    need_sync: bool
    desired_revision: int


@dataclass(frozen=True)
class ReportScreenPlaybackEventsResult:
    stored_count: int
    duplicate_count: int
