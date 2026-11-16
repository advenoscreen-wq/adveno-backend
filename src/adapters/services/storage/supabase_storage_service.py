"""Supabase Storage implementation of the storage service port."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote, urlencode

import httpx

from application.exceptions.storage import StorageServiceError

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    def __init__(
        self,
        *,
        supabase_url: str,
        supabase_anon_key: str,
        timeout_seconds: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = supabase_url.rstrip("/")
        self.anon_key = supabase_anon_key
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def create_signed_upload_url(
        self,
        *,
        bucket: str,
        object_path: str,
        access_token: str,
    ) -> str:
        self._validate_upload_target(bucket, object_path, access_token)
        operation = {"bucket": bucket}
        endpoint = (
            "/storage/v1/object/upload/sign/"
            f"{quote(bucket, safe='')}/{quote(object_path, safe='/')}"
        )
        logger.info("Supabase signed upload URL request started", extra=operation)
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    endpoint,
                    headers={
                        "apikey": self.anon_key,
                        "Authorization": f"Bearer {access_token}",
                    },
                )
            response.raise_for_status()
            signed_url = self._extract_signed_url(response.json(), endpoint)
            logger.info("Supabase signed upload URL created", extra=operation)
            return signed_url
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            logger.warning(
                "Supabase signed upload URL request failed",
                extra={**operation, "error_type": type(error).__name__},
            )
            raise StorageServiceError() from error

    def _extract_signed_url(self, data: Any, endpoint: str) -> str:
        if not isinstance(data, dict):
            raise TypeError("Supabase Storage response must be an object")

        response_url = data.get("signedUrl") or data.get("signedURL") or data.get("url")
        if isinstance(response_url, str) and response_url:
            if response_url.startswith(("https://", "http://")):
                return response_url
            if response_url.startswith("/storage/v1/"):
                return f"{self.base_url}{response_url}"
            if response_url.startswith("/"):
                return f"{self.base_url}/storage/v1{response_url}"
            return f"{self.base_url}/storage/v1/{response_url}"

        token = data.get("token")
        if isinstance(token, str) and token:
            return f"{self.base_url}{endpoint}?{urlencode({'token': token})}"
        raise KeyError("Supabase Storage response did not include an upload URL")

    @staticmethod
    def _validate_upload_target(bucket: str, object_path: str, access_token: str) -> None:
        if not bucket.strip() or "/" in bucket:
            raise ValueError("bucket must be a non-empty bucket name")
        if (
            not object_path.strip()
            or object_path.startswith("/")
            or any(segment in ("", ".", "..") for segment in object_path.split("/"))
        ):
            raise ValueError("object_path must be a relative object path")
        if not access_token.strip():
            raise ValueError("access_token is required")
