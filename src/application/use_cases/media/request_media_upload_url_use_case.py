"""Create a signed upload URL for a new media object."""

from uuid import uuid4

from application.exceptions.media import InvalidMediaUploadRequestError
from application.use_cases.media.commands import RequestMediaUploadUrlCommand
from application.use_cases.media.results import RequestMediaUploadUrlResult
from ports.services.storage_service import StorageService


class RequestMediaUploadUrlUseCase:
    def __init__(self, *, storage_service: StorageService, bucket: str) -> None:
        self._storage_service = storage_service
        self._bucket = bucket

    async def __call__(self, command: RequestMediaUploadUrlCommand) -> RequestMediaUploadUrlResult:
        file_name = command.file_name.strip()
        if (
            not file_name
            or file_name in {".", ".."}
            or "/" in file_name
            or "\\" in file_name
            or "\x00" in file_name
        ):
            raise InvalidMediaUploadRequestError()

        storage_path = f"users/{command.user_id}/{uuid4().hex}/{file_name}"
        signed_url = await self._storage_service.create_signed_upload_url(
            bucket=self._bucket,
            object_path=storage_path,
            access_token=command.access_token,
        )
        return RequestMediaUploadUrlResult(
            signed_url=signed_url,
            storage_path=storage_path,
        )
