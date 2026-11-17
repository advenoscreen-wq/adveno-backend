"""Screen pairing request routes."""

from uuid import UUID

from fastapi import APIRouter, Header, status

from application.use_cases.pairing.commands import (
    ApproveScreenPairingSessionCommand,
    CreatePairedScreenCommand,
    CreateScreenPairingSessionCommand,
    GetScreenPairingSessionStatusCommand,
    IssuePairedScreenCredentialCommand,
    VerifyScreenPairingSessionCommand,
)
from drivers.routers.dependencies import CurrentUser
from drivers.routers.pairing.dependencies import (
    ApproveScreenPairingSession,
    CreatePairedScreen,
    CreateScreenPairingSession,
    GetScreenPairingSessionStatus,
    IssuePairedScreenCredential,
    VerifyScreenPairingSession,
)
from drivers.schemas.pairing import (
    ApproveScreenPairingSessionRequest,
    ApproveScreenPairingSessionResponse,
    CreatePairedScreenRequest,
    CreatePairedScreenResponse,
    CreateScreenPairingSessionRequest,
    CreateScreenPairingSessionResponse,
    IssuePairedScreenCredentialResponse,
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
    result = await use_case(CreateScreenPairingSessionCommand(pairing_type=body.pairing_type))
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
    result = await use_case(VerifyScreenPairingSessionCommand(pairing_token=pairing_token))
    return VerifyScreenPairingSessionResponse(
        session_id=result.session_id,
        status=result.status,
        pairing_type=result.pairing_type,
        screen_id=result.screen_id,
        screen_exists=result.screen_exists,
        expires_at=result.expires_at,
        created_at=result.created_at,
    )


@router.post("/sessions/approve", response_model=ApproveScreenPairingSessionResponse)
async def approve_screen_pairing_session(
    body: ApproveScreenPairingSessionRequest,
    current_user: CurrentUser,
    use_case: ApproveScreenPairingSession,
    pairing_token: str = Header(alias="X-Pairing-Token"),
) -> ApproveScreenPairingSessionResponse:
    result = await use_case(
        ApproveScreenPairingSessionCommand(
            pairing_token=pairing_token,
            user_id=current_user.id,
            screen_id=body.screen_id,
        )
    )
    return ApproveScreenPairingSessionResponse(
        session_id=result.session_id,
        pairing_type=result.pairing_type,
        status=result.status,
        screen_id=result.screen_id,
        paired_at=result.paired_at,
    )


@router.post(
    "/sessions/{session_id}/screen",
    status_code=status.HTTP_201_CREATED,
    response_model=CreatePairedScreenResponse,
)
async def create_paired_screen(
    session_id: UUID,
    body: CreatePairedScreenRequest,
    current_user: CurrentUser,
    use_case: CreatePairedScreen,
    pairing_token: str = Header(alias="X-Pairing-Token"),
) -> CreatePairedScreenResponse:
    result = await use_case(
        CreatePairedScreenCommand(
            session_id=session_id,
            pairing_token=pairing_token,
            user_id=current_user.id,
            name=body.name,
            device_model=body.device_model,
            app_version=body.app_version,
        )
    )
    return CreatePairedScreenResponse(
        screen_id=result.screen_id,
        screen_code=result.screen_code,
        name=result.name,
        credential=result.credential,
    )


@router.post(
    "/sessions/{session_id}/credential",
    response_model=IssuePairedScreenCredentialResponse,
)
async def issue_paired_screen_credential(
    session_id: UUID,
    use_case: IssuePairedScreenCredential,
    pairing_token: str = Header(alias="X-Pairing-Token"),
) -> IssuePairedScreenCredentialResponse:
    result = await use_case(
        IssuePairedScreenCredentialCommand(
            session_id=session_id,
            pairing_token=pairing_token,
        )
    )
    return IssuePairedScreenCredentialResponse(
        screen_id=result.screen_id,
        credential=result.credential,
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
