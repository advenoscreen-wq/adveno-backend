"""Application port for cloud object storage operations."""

from typing import Protocol


class StorageService(Protocol):
    def get_public_url(self, *, bucket: str, object_path: str) -> str: ...

    async def create_signed_upload_url(
        self,
        *,
        bucket: str,
        object_path: str,
        access_token: str,
        upsert: bool = False,
    ) -> str: ...
