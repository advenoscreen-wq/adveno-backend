"""Media upload routes."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from application.use_cases.media.commands import (
    CreateMediaAssetCommand,
    RequestMediaReplacementUploadUrlCommand,
    RequestMediaUploadUrlCommand,
    UpdateMediaAndSyncCommand,
)
from drivers.routers.dependencies import (
    AuthenticatedAccessToken,
    CurrentUser,
)
from drivers.routers.media.dependencies import (
    CreateMediaAsset,
    GetMediaAsset,
    ListMediaAssets,
    RequestMediaReplacementUploadUrl,
    RequestMediaUploadUrl,
    UpdateMediaAndSync,
)
from drivers.schemas.common import PaginationResponse
from drivers.schemas.media import (
    CreateMediaAssetRequest,
    MediaAssetResponse,
    RequestMediaUploadUrlRequest,
    RequestMediaUploadUrlResponse,
    UpdateMediaAndSyncRequest,
    UpdateMediaAndSyncResponse,
)

router = APIRouter(prefix="/media", tags=["media"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginationResponse[MediaAssetResponse],
)
async def list_media_assets(
    current_user: CurrentUser,
    use_case: ListMediaAssets,
    filter_by_name: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginationResponse[MediaAssetResponse]:
    result = await use_case(
        user_id=current_user.id,
        filter_by_name=filter_by_name,
        page=page,
        limit=limit,
    )
    return PaginationResponse[MediaAssetResponse](
        items=result.items,
        total_pages=result.total_pages,
        total_items=result.total_items,
        has_next=result.has_next,
        has_prev=result.has_prev,
        limit=result.limit,
        page=result.page,
    )


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
    return MediaAssetResponse.from_result(result)


@router.get(
    "/{media_id}",
    status_code=status.HTTP_200_OK,
    response_model=MediaAssetResponse,
)
async def get_media_asset(
    media_id: UUID,
    current_user: CurrentUser,
    use_case: GetMediaAsset,
) -> MediaAssetResponse:
    result = await use_case(media_id=media_id, user_id=current_user.id)
    return MediaAssetResponse.from_result(result)


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
    return UpdateMediaAndSyncResponse.from_result(result)
