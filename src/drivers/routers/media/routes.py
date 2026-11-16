"""Media upload routes."""

from uuid import UUID

from fastapi import APIRouter, status

from application.use_cases.media.commands import (
    CreateMediaAssetCommand,
    RequestMediaReplacementUploadUrlCommand,
    RequestMediaUploadUrlCommand,
    UpdateMediaAndSyncCommand,
)
from drivers.routers.dependencies import (
    AuthenticatedAccessToken,
    CurrentUser,
    SettingsDependency,
)
from drivers.routers.media.dependencies import (
    CreateMediaAsset,
    GetMediaAsset,
    RequestMediaReplacementUploadUrl,
    RequestMediaUploadUrl,
    StorageServiceDependency,
    UpdateMediaAndSync,
)
from drivers.schemas.media import (
    CreateMediaAssetRequest,
    MediaAssetResponse,
    RequestMediaUploadUrlRequest,
    RequestMediaUploadUrlResponse,
    ScreenSyncRevision,
    UpdateMediaAndSyncRequest,
    UpdateMediaAndSyncResponse,
)

router = APIRouter(prefix="/media", tags=["media"])


@router.post(
    "/upload-url",
    status_code=status.HTTP_200_OK,
    response_model=RequestMediaUploadUrlResponse,
)
async def request_media_upload_url(
    body: RequestMediaUploadUrlRequest,
    current_user: CurrentUser,
    access_token: AuthenticatedAccessToken,
    use_case: RequestMediaUploadUrl,
) -> RequestMediaUploadUrlResponse:
    result = await use_case(
        RequestMediaUploadUrlCommand(
            user_id=current_user.id,
            file_name=body.file_name,
            access_token=access_token,
        )
    )
    return RequestMediaUploadUrlResponse(
        signed_url=result.signed_url,
        storage_path=result.storage_path,
    )


@router.post(
    "/{media_id}/upload-url",
    status_code=status.HTTP_200_OK,
    response_model=RequestMediaUploadUrlResponse,
)
async def request_media_replacement_upload_url(
    media_id: UUID,
    current_user: CurrentUser,
    access_token: AuthenticatedAccessToken,
    use_case: RequestMediaReplacementUploadUrl,
) -> RequestMediaUploadUrlResponse:
    result = await use_case(
        RequestMediaReplacementUploadUrlCommand(
            media_id=media_id,
            user_id=current_user.id,
            access_token=access_token,
        )
    )
    return RequestMediaUploadUrlResponse(
        signed_url=result.signed_url,
        storage_path=result.storage_path,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MediaAssetResponse,
)
async def create_media_asset(
    body: CreateMediaAssetRequest,
    current_user: CurrentUser,
    use_case: CreateMediaAsset,
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> MediaAssetResponse:
    result = await use_case(
        CreateMediaAssetCommand(
            user_id=current_user.id,
            name=body.name,
            media_type=body.media_type,
            mime_type=body.mime_type,
            storage_path=body.storage_path,
            file_size=body.file_size,
            width=body.width,
            height=body.height,
            duration_seconds=body.duration_seconds,
        )
    )
    return MediaAssetResponse(
        **vars(result.media),
        media_url=storage_service.get_public_url(
            bucket=settings.media_storage_bucket,
            object_path=result.media.storage_path,
        ),
    )


@router.get(
    "/{media_id}",
    status_code=status.HTTP_200_OK,
    response_model=MediaAssetResponse,
)
async def get_media_asset(
    media_id: UUID,
    current_user: CurrentUser,
    use_case: GetMediaAsset,
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> MediaAssetResponse:
    media = await use_case(media_id=media_id, user_id=current_user.id)
    return MediaAssetResponse(
        **vars(media),
        media_url=storage_service.get_public_url(
            bucket=settings.media_storage_bucket,
            object_path=media.storage_path,
        ),
    )


@router.put(
    "/{media_id}",
    status_code=status.HTTP_200_OK,
    response_model=UpdateMediaAndSyncResponse,
)
async def update_media_and_sync(
    media_id: UUID,
    body: UpdateMediaAndSyncRequest,
    current_user: CurrentUser,
    use_case: UpdateMediaAndSync,
    storage_service: StorageServiceDependency,
    settings: SettingsDependency,
) -> UpdateMediaAndSyncResponse:
    result = await use_case(
        UpdateMediaAndSyncCommand(
            media_id=media_id,
            user_id=current_user.id,
            is_replaced=body.is_replaced,
            name=body.name,
            media_type=body.media_type,
            mime_type=body.mime_type,
            storage_path=body.storage_path,
            file_size=body.file_size,
            width=body.width,
            height=body.height,
            duration_seconds=body.duration_seconds,
        )
    )
    return UpdateMediaAndSyncResponse(
        **vars(result.media),
        media_url=storage_service.get_public_url(
            bucket=settings.media_storage_bucket,
            object_path=result.media.storage_path,
        ),
        screen_sync=[
            ScreenSyncRevision(
                screen_id=state.screen_id,
                desired_revision=state.desired_revision,
            )
            for state in result.sync_states
        ],
    )
