"""Screen pairing request routes."""

from uuid import UUID

from fastapi import APIRouter, Header, status

from application.use_cases.pairing.commands import (
    CreateScreenPairingSessionCommand,
    GetScreenPairingSessionStatusCommand,
    VerifyScreenPairingSessionCommand,
)
from drivers.routers.dependencies import CurrentUser
from drivers.routers.pairing.dependencies import (
    CreateScreenPairingSession,
    GetScreenPairingSessionStatus,
    VerifyScreenPairingSession,
)
from drivers.schemas.pairing import (
    CreateScreenPairingSessionRequest,
    CreateScreenPairingSessionResponse,
    ScreenPairingSessionStatusResponse,
    VerifyScreenPairingSessionResponse,
)

router = APIRouter(prefix="/pairing", tags=["pairing"])


@router.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateScreenPairingSessionResponse,
)
async def create_screen_pairing_session(
    body: CreateScreenPairingSessionRequest,
    use_case: CreateScreenPairingSession,
) -> CreateScreenPairingSessionResponse:
    result = await use_case(
        CreateScreenPairingSessionCommand(pairing_type=body.pairing_type)
    )
    return CreateScreenPairingSessionResponse(
        session_id=result.session_id,
        pairing_token=result.pairing_token,
        expires_at=result.expires_at,
    )


@router.get("/sessions/verify", response_model=VerifyScreenPairingSessionResponse)
async def verify_screen_pairing_session(
    current_user: CurrentUser,
    use_case: VerifyScreenPairingSession,
    pairing_token: str = Header(alias="X-Pairing-Token"),
) -> VerifyScreenPairingSessionResponse:
    result = await use_case(
        VerifyScreenPairingSessionCommand(pairing_token=pairing_token)
    )
    return VerifyScreenPairingSessionResponse(
        session_id=result.session_id,
        status=result.status,
        pairing_type=result.pairing_type,
        screen_id=result.screen_id,
        screen_exists=result.screen_exists,
        expires_at=result.expires_at,
        created_at=result.created_at,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=ScreenPairingSessionStatusResponse,
)
async def get_screen_pairing_session_status(
    session_id: UUID,
    use_case: GetScreenPairingSessionStatus,
    pairing_token: str = Header(alias="X-Pairing-Token"),
) -> ScreenPairingSessionStatusResponse:
    result = await use_case(
        GetScreenPairingSessionStatusCommand(
            session_id=session_id,
            pairing_token=pairing_token,
        )
    )
    return ScreenPairingSessionStatusResponse(status=result.status)
