"""Screen management routes for the user-facing app."""

from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from application.use_cases.screens.commands import (
    AcknowledgeScreenSyncCommand,
    CreateScreenAdminSessionCommand,
    PlaybackEventData,
    ReportScreenPlaybackEventsCommand,
    VerifyScreenAdminSessionCommand,
)
from drivers.routers.dependencies import CurrentUser
from drivers.routers.screens.dependencies import (
    AcknowledgeScreenSync,
    AssignPlaylist,
    CheckScreenSync,
    CreateScreenAdminSession,
    DeleteScreen,
    DisconnectScreen,
    GetAssignedPlaylist,
    GetScreen,
    ListScreens,
    LogoutScreen,
    ProtectedScreenAdminSessionDependency,
    ReportScreenPlaybackEvents,
    RevokeScreenAdminSession,
    ScreenDeviceCredential,
    UnassignPlaylist,
    UpdateScreen,
    VerifyScreenAdminSession,
    VerifyScreenCredential,
)
from drivers.schemas.common import PaginationResponse
from drivers.schemas.playlists import PlaylistResponse
from drivers.schemas.screens import (
    AssignedScreenPlaylistResponse,
    AssignPlaylistRequest,
    CreateScreenAdminSessionResponse,
    ReportScreenPlaybackEventsRequest,
    ReportScreenPlaybackEventsResponse,
    ScreenCredentialVerificationResponse,
    ScreenListItemResponse,
    ScreenPlaylistAssignmentResponse,
    ScreenResponse,
    ScreenSyncAcknowledgmentRequest,
    ScreenSyncCheckResponse,
    UpdateScreenRequest,
    UpdateScreenResponse,
    VerifyScreenAdminSessionRequest,
    VerifyScreenAdminSessionResponse,
)

router = APIRouter(prefix="/screens", tags=["screens"])


@router.post(
    "/credential/verify",
    response_model=ScreenCredentialVerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_screen_credential(
    use_case: VerifyScreenCredential,
    credential: ScreenDeviceCredential,
) -> ScreenCredentialVerificationResponse:
    """Check whether the TV's stored device credential is still active."""
    await use_case(credential=credential)
    return ScreenCredentialVerificationResponse(valid=True)


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
    result = await use_case(credential=credential)
    return ScreenSyncCheckResponse(
        need_sync=result.need_sync,
        desired_revision=result.desired_revision,
    )


@router.get(
    "/assigned-playlist",
    response_model=AssignedScreenPlaylistResponse,
    status_code=status.HTTP_200_OK,
)
async def get_assigned_playlist(
    use_case: GetAssignedPlaylist,
    credential: ScreenDeviceCredential,
) -> AssignedScreenPlaylistResponse:
    """Return the authenticated TV's assigned playlist and media metadata."""
    result = await use_case(credential=credential)
    return AssignedScreenPlaylistResponse.model_validate(result, from_attributes=True)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_screen(
    use_case: LogoutScreen,
    authorization: ProtectedScreenAdminSessionDependency,
) -> Response:
    """Revoke the TV credential after protected-session authorization."""
    await use_case(authorization)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{screen_id}/admin-session",
    response_model=CreateScreenAdminSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_screen_admin_session(
    screen_id: UUID,
    current_user: CurrentUser,
    use_case: CreateScreenAdminSession,
) -> CreateScreenAdminSessionResponse:
    """Generate a one-time PIN for the selected screen's settings."""
    result = await use_case(
        CreateScreenAdminSessionCommand(screen_id=screen_id, user_id=current_user.id)
    )
    return CreateScreenAdminSessionResponse(
        session_id=result.session_id,
        pin=result.pin,
        expires_at=result.expires_at,
    )


@router.post(
    "/admin-session/verify",
    response_model=VerifyScreenAdminSessionResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_screen_admin_session(
    body: VerifyScreenAdminSessionRequest,
    use_case: VerifyScreenAdminSession,
    credential: ScreenDeviceCredential,
) -> VerifyScreenAdminSessionResponse:
    """Verify a dashboard PIN and issue a temporary TV settings token."""
    result = await use_case(
        credential=credential,
        command=VerifyScreenAdminSessionCommand(pin=body.pin),
    )
    return VerifyScreenAdminSessionResponse(
        session_id=result.session_id,
        session_token=result.session_token,
        expires_at=result.expires_at,
    )


@router.post(
    "/admin-session/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_screen_admin_session(
    use_case: RevokeScreenAdminSession,
    authorization: ProtectedScreenAdminSessionDependency,
) -> Response:
    """Revoke this TV's temporary settings access."""
    await use_case(authorization)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/sync-acknowledgments",
    status_code=status.HTTP_202_ACCEPTED,
)
async def acknowledge_screen_sync(
    body: ScreenSyncAcknowledgmentRequest,
    use_case: AcknowledgeScreenSync,
    credential: ScreenDeviceCredential,
) -> Response:
    """Persist the revision the TV reports as successfully applied."""
    await use_case(
        credential=credential,
        command=AcknowledgeScreenSyncCommand(applied_revision=body.applied_revision),
    )
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post(
    "/playback-events",
    response_model=ReportScreenPlaybackEventsResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def report_screen_playback_events(
    body: ReportScreenPlaybackEventsRequest,
    use_case: ReportScreenPlaybackEvents,
    credential: ScreenDeviceCredential,
) -> ReportScreenPlaybackEventsResponse:
    """Store completed ad playback events reported by this screen."""
    result = await use_case(
        credential=credential,
        command=ReportScreenPlaybackEventsCommand(
            events=[
                PlaybackEventData(
                    event_id=event.event_id,
                    playlist_id=event.playlist_id,
                    playlist_item_id=event.playlist_item_id,
                    media_asset_id=event.media_asset_id,
                    playlist_version=event.playlist_version,
                    media_checksum=event.media_checksum,
                    played_at=event.played_at,
                    played_complete_at=event.played_complete_at,
                )
                for event in body.events
            ]
        ),
    )
    return ReportScreenPlaybackEventsResponse(
        stored_count=result.stored_count,
        duplicate_count=result.duplicate_count,
    )


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
