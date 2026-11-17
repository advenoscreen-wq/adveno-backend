"""Screen management routes for the user-facing app."""

from uuid import UUID

from fastapi import APIRouter, status

from drivers.routers.dependencies import CurrentUser
from drivers.routers.screens.dependencies import UpdateScreen
from drivers.schemas.screens import UpdateScreenRequest, UpdateScreenResponse

router = APIRouter(prefix="/screens", tags=["screens"])


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
