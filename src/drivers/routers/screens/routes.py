"""Screen management routes for the user-facing app."""

from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from drivers.routers.dependencies import CurrentUser
from drivers.routers.screens.dependencies import (
    AssignPlaylist,
    CheckScreenSync,
    DeleteScreen,
    DisconnectScreen,
    GetScreen,
    ListScreens,
    ScreenDeviceCredential,
    UnassignPlaylist,
    UpdateScreen,
)
from drivers.schemas.common import PaginationResponse
from drivers.schemas.playlists import PlaylistResponse
from drivers.schemas.screens import (
    AssignPlaylistRequest,
    ScreenListItemResponse,
    ScreenPlaylistAssignmentResponse,
    ScreenResponse,
    ScreenSyncCheckResponse,
    UpdateScreenRequest,
    UpdateScreenResponse,
)

router = APIRouter(prefix="/screens", tags=["screens"])


@router.post(
    "/sync-check",
    response_model=ScreenSyncCheckResponse,
    status_code=status.HTTP_200_OK,
)
async def check_screen_sync(
    use_case: CheckScreenSync,
    credential: ScreenDeviceCredential,
) -> ScreenSyncCheckResponse:
    """Record a TV heartbeat and report whether it needs to fetch updates."""
    need_sync = await use_case(credential=credential)
    return ScreenSyncCheckResponse(need_sync=need_sync)


@router.get(
    "",
    response_model=PaginationResponse[ScreenListItemResponse],
    status_code=status.HTTP_200_OK,
)
async def list_screens(
    current_user: CurrentUser,
    use_case: ListScreens,
    filter_by_name: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginationResponse[ScreenListItemResponse]:
    result = await use_case(
        user_id=current_user.id,
        filter_by_name=filter_by_name,
        page=page,
        limit=limit,
    )
    return PaginationResponse[ScreenListItemResponse](
        items=[
            ScreenListItemResponse.model_validate(screen, from_attributes=True)
            for screen in result.items
        ],
        total_pages=result.total_pages,
        total_items=result.total_items,
        has_next=result.has_next,
        has_prev=result.has_prev,
        limit=result.limit,
        page=result.page,
    )


@router.get("/{screen_id}", response_model=ScreenResponse, status_code=status.HTTP_200_OK)
async def get_screen(
    screen_id: UUID,
    current_user: CurrentUser,
    use_case: GetScreen,
) -> ScreenResponse:
    result = await use_case(screen_id=screen_id, user_id=current_user.id)
    return ScreenResponse(
        id=result.screen.id,
        screen_code=result.screen.screen_code,
        name=result.screen.name,
        status=result.screen.status,
        updated_at=result.screen.updated_at,
        assigned_playlist=(
            PlaylistResponse.from_entity(result.assigned_playlist)
            if result.assigned_playlist is not None
            else None
        ),
    )


@router.put(
    "/{screen_id}/playlist",
    response_model=ScreenPlaylistAssignmentResponse,
    status_code=status.HTTP_200_OK,
)
async def assign_playlist(
    screen_id: UUID,
    body: AssignPlaylistRequest,
    current_user: CurrentUser,
    use_case: AssignPlaylist,
) -> ScreenPlaylistAssignmentResponse:
    assignment = await use_case(
        screen_id=screen_id,
        playlist_id=body.playlist_id,
        user_id=current_user.id,
    )
    return ScreenPlaylistAssignmentResponse(
        id=assignment.id,
        screen_id=assignment.screen_id,
        playlist_id=assignment.playlist_id,
        assigned_at=assignment.assigned_at,
    )


@router.delete(
    "/{screen_id}/playlist",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unassign_playlist(
    screen_id: UUID,
    current_user: CurrentUser,
    use_case: UnassignPlaylist,
) -> Response:
    await use_case(screen_id=screen_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{screen_id}", response_model=UpdateScreenResponse, status_code=status.HTTP_200_OK)
async def update_screen(
    screen_id: UUID,
    body: UpdateScreenRequest,
    current_user: CurrentUser,
    use_case: UpdateScreen,
) -> UpdateScreenResponse:
    screen = await use_case(
        screen_id=screen_id,
        user_id=current_user.id,
        name=body.name,
    )
    return UpdateScreenResponse(
        id=screen.id,
        screen_code=screen.screen_code,
        name=screen.name,
        status=screen.status,
        updated_at=screen.updated_at,
    )


@router.post(
    "/{screen_id}/disconnect",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def disconnect_screen(
    screen_id: UUID,
    current_user: CurrentUser,
    use_case: DisconnectScreen,
) -> Response:
    await use_case(screen_id=screen_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{screen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_screen(
    screen_id: UUID,
    current_user: CurrentUser,
    use_case: DeleteScreen,
) -> Response:
    await use_case(screen_id=screen_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
