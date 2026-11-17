"""Replace a playlist's details and ordered media items, then notify its screens."""

from application.exceptions.media import MediaNotFoundError
from application.exceptions.playlist import InvalidPlaylistRequestError, PlaylistNotFoundError
from application.use_cases.playlists.commands import UpdatePlaylistCommand
from domain import Playlist, PlaylistItem
from domain.exceptions import DomainError
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.repositories.playlist_item_repository import PlaylistItemRepository
from ports.repositories.playlist_repository import PlaylistRepository
from ports.repositories.screen_playlist_assignment_repository import (
    ScreenPlaylistAssignmentRepository,
)
from ports.repositories.screen_sync_state_repository import ScreenSyncStateRepository


class UpdatePlaylistUseCase:
    def __init__(
        self,
        *,
        playlist_repository: PlaylistRepository,
        playlist_item_repository: PlaylistItemRepository,
        media_repository: MediaAssetRepository,
        assignment_repository: ScreenPlaylistAssignmentRepository,
        sync_state_repository: ScreenSyncStateRepository,
    ) -> None:
        self._playlist_repository = playlist_repository
        self._playlist_item_repository = playlist_item_repository
        self._media_repository = media_repository
        self._assignment_repository = assignment_repository
        self._sync_state_repository = sync_state_repository

    async def __call__(self, command: UpdatePlaylistCommand) -> Playlist:
        playlist = await self._playlist_repository.get_by_id(
            command.playlist_id,
            user_id=command.user_id,
        )
        if playlist is None:
            raise PlaylistNotFoundError()

        media_assets = []
        for item_command in command.items:
            media = await self._media_repository.get_by_id(
                item_command.media_asset_id,
                user_id=command.user_id,
            )
            if media is None:
                raise MediaNotFoundError()
            media_assets.append(media)

        try:
            playlist.rename(command.name)
            playlist.update_description(command.description)
            playlist_items = [
                PlaylistItem(
                    playlist_id=playlist.id,
                    media_asset_id=item_command.media_asset_id,
                    position=item_command.position,
                    duration_seconds=item_command.duration_seconds,
                )
                for item_command in command.items
            ]
            playlist.replace_items(list(zip(playlist_items, media_assets, strict=True)))
        except DomainError as error:
            raise InvalidPlaylistRequestError() from error

        await self._playlist_repository.update(playlist)
        await self._playlist_item_repository.delete_by_playlist_id(playlist.id)
        for playlist_item in playlist.items:
            await self._playlist_item_repository.save(playlist_item)

        assignments = await self._assignment_repository.list_active_by_playlist_ids([playlist.id])
        screen_ids = sorted({assignment.screen_id for assignment in assignments}, key=str)
        for screen_id in screen_ids:
            await self._sync_state_repository.increment_desired_revision(screen_id)

        return playlist
