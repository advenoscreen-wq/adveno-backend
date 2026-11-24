"""Persist completed playback reports from an authenticated screen."""

from application.use_cases.screens.commands import (
    ReportScreenPlaybackEventsCommand,
)
from application.use_cases.screens.results import ReportScreenPlaybackEventsResult
from application.use_cases.screens.screen_device_auth import authenticate_screen_device
from domain import ScreenPlaybackEvent
from ports.repositories.screen_credential_repository import ScreenCredentialRepository
from ports.repositories.screen_playback_event_repository import ScreenPlaybackEventRepository
from ports.repositories.screen_repository import ScreenRepository


class ReportScreenPlaybackEventsUseCase:
    def __init__(
        self,
        *,
        screen_repository: ScreenRepository,
        credential_repository: ScreenCredentialRepository,
        playback_event_repository: ScreenPlaybackEventRepository,
    ) -> None:
        self._screen_repository = screen_repository
        self._credential_repository = credential_repository
        self._playback_event_repository = playback_event_repository

    async def __call__(
        self,
        *,
        credential: str,
        command: ReportScreenPlaybackEventsCommand,
    ) -> ReportScreenPlaybackEventsResult:
        screen = await authenticate_screen_device(
            credential=credential,
            screen_repository=self._screen_repository,
            credential_repository=self._credential_repository,
        )
        events = [
            ScreenPlaybackEvent(
                screen_id=screen.id,
                event_id=event.event_id,
                playlist_id=event.playlist_id,
                playlist_item_id=event.playlist_item_id,
                media_asset_id=event.media_asset_id,
                playlist_version=event.playlist_version,
                media_checksum=event.media_checksum,
                played_at=event.played_at,
                played_complete_at=event.played_complete_at,
            )
            for event in command.events
        ]
        stored_count = await self._playback_event_repository.save_many_idempotently(events)
        return ReportScreenPlaybackEventsResult(
            stored_count=stored_count,
            duplicate_count=len(events) - stored_count,
        )
