"""Playlist management routes for authenticated users."""

from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from application.use_cases.playlists.commands import (
    CreatePlaylistCommand,
    CreatePlaylistItemCommand,
    UpdatePlaylistCommand,
)
from drivers.routers.dependencies import CurrentUser
from drivers.routers.playlists.dependencies import (
    CreatePlaylist,
    DeletePlaylist,
    GetPlaylist,
    ListPlaylists,
    UpdatePlaylist,
)
from drivers.schemas.common import PaginationResponse
from drivers.schemas.playlists import (
    CreatePlaylistRequest,
    PlaylistResponse,
    UpdatePlaylistRequest,
)

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaylistResponse,
)
async def create_playlist(
    body: CreatePlaylistRequest,
    current_user: CurrentUser,
    use_case: CreatePlaylist,
) -> PlaylistResponse:
    playlist = await use_case(
        CreatePlaylistCommand(
            user_id=current_user.id,
            name=body.name,
            description=body.description,
            items=[
                CreatePlaylistItemCommand(
                    media_asset_id=item.media_asset_id,
                    position=item.position,
                    duration_seconds=item.duration_seconds,
                )
                for item in body.items
            ],
        )
    )
    return PlaylistResponse.from_entity(playlist)


@router.get(
    "/{playlist_id}",
    status_code=status.HTTP_200_OK,
    response_model=PlaylistResponse,
)
async def get_playlist(
    playlist_id: UUID,
    current_user: CurrentUser,
    use_case: GetPlaylist,
) -> PlaylistResponse:
    playlist = await use_case(playlist_id=playlist_id, user_id=current_user.id)
    return PlaylistResponse.from_entity(playlist)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginationResponse[PlaylistResponse],
)
async def list_playlists(
    current_user: CurrentUser,
    use_case: ListPlaylists,
    filter_by_title: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginationResponse[PlaylistResponse]:
    result = await use_case(
        user_id=current_user.id,
        filter_by_title=filter_by_title,
        page=page,
        limit=limit,
    )
    playlist_responses = [PlaylistResponse.from_entity(playlist) for playlist in result.items]
    return PaginationResponse[PlaylistResponse](
        items=playlist_responses,
        total_pages=result.total_pages,
        total_items=result.total_items,
        has_next=result.has_next,
        has_prev=result.has_prev,
        limit=result.limit,
        page=result.page,
    )


@router.put(
    "/{playlist_id}",
    status_code=status.HTTP_200_OK,
    response_model=PlaylistResponse,
)
async def update_playlist(
    playlist_id: UUID,
    body: UpdatePlaylistRequest,
    current_user: CurrentUser,
    use_case: UpdatePlaylist,
) -> PlaylistResponse:
    playlist = await use_case(
        UpdatePlaylistCommand(
            playlist_id=playlist_id,
            user_id=current_user.id,
            name=body.name,
            description=body.description,
            items=[
                CreatePlaylistItemCommand(
                    media_asset_id=item.media_asset_id,
                    position=item.position,
                    duration_seconds=item.duration_seconds,
                )
                for item in body.items
            ],
        )
    )
    return PlaylistResponse.from_entity(playlist)


@router.delete(
    "/{playlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_playlist(
    playlist_id: UUID,
    current_user: CurrentUser,
    use_case: DeletePlaylist,
) -> Response:
    await use_case(playlist_id=playlist_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
