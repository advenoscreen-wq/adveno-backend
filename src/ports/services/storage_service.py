"""Application port for cloud object storage operations."""

from typing import Protocol


class StorageService(Protocol):
    async def create_signed_upload_url(
        self,
        *,
        bucket: str,
        object_path: str,
        access_token: str,
    ) -> str: ...
