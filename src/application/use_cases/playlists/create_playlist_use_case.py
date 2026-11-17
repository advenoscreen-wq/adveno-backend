"""Create a playlist with media selected by its owner."""

from application.exceptions.media import MediaNotFoundError
from application.exceptions.playlist import InvalidPlaylistRequestError
from application.use_cases.playlists.commands import CreatePlaylistCommand
from domain import Playlist, PlaylistItem
from domain.exceptions import DomainError
from ports.repositories.media_asset_repository import MediaAssetRepository
from ports.repositories.playlist_item_repository import PlaylistItemRepository
from ports.repositories.playlist_repository import PlaylistRepository


class CreatePlaylistUseCase:
    def __init__(
        self,
        *,
        playlist_repository: PlaylistRepository,
        playlist_item_repository: PlaylistItemRepository,
        media_repository: MediaAssetRepository,
    ) -> None:
        self._playlist_repository = playlist_repository
        self._playlist_item_repository = playlist_item_repository
        self._media_repository = media_repository

    async def __call__(self, command: CreatePlaylistCommand) -> Playlist:
        media_assets = []
        for item_command in command.items:
            media = await self._media_repository.get_by_id(
                item_command.media_asset_id,
                user_id=command.user_id,
            )
            if media is None:
                raise MediaNotFoundError()
            media_assets.append(media)

        playlist = Playlist(
            name=command.name,
            description=command.description,
            user_id=command.user_id,
        )
        try:
            playlist_items = [
                PlaylistItem(
                    playlist_id=playlist.id,
                    media_asset_id=command_item.media_asset_id,
                    position=command_item.position,
                    duration_seconds=command_item.duration_seconds,
                )
                for command_item in command.items
            ]
            for playlist_item, media in zip(playlist_items, media_assets, strict=True):
                playlist.add_item(playlist_item, media)
        except DomainError as error:
            raise InvalidPlaylistRequestError() from error

        await self._playlist_repository.save(playlist)
        for playlist_item in playlist.items:
            await self._playlist_item_repository.save(playlist_item)
        return playlist
