"""Supabase implementation of the provider-independent OAuth port."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from urllib.parse import urlencode

import httpx

from application.dtos.oauth import OAuthTokenResult, OAuthUserInfo
from application.exceptions.oauth import OAuthProviderError


class SupabaseOAuthAdapter:
    def __init__(
        self,
        *,
        supabase_url: str,
        supabase_anon_key: str,
        provider: str = "google",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.base_url = supabase_url.rstrip("/")
        self.anon_key = supabase_anon_key
        self.provider = provider
        self.timeout_seconds = timeout_seconds

    async def get_authorization_url(
        self,
        *,
        redirect_uri: str,
        state: str,
        scopes: list[str] | None = None,
    ) -> str:
        params = {
            "provider": self.provider,
            "redirect_to": redirect_uri,
            "state": state,
        }
        if scopes:
            params["scopes"] = " ".join(scopes)
        return f"{self.base_url}/auth/v1/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str, *, redirect_uri: str) -> OAuthTokenResult:
        return await self._token_request(
            grant_type="authorization_code",
            payload={"code": code, "redirect_uri": redirect_uri},
        )

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResult:
        result = await self._token_request(
            grant_type="refresh_token",
            payload={"refresh_token": refresh_token},
        )
        return (
            result
            if result.refresh_token is not None
            else replace(result, refresh_token=refresh_token)
        )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        response = await self._request(
            "GET",
            "/auth/v1/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = response.json()
        user_metadata = data.get("user_metadata") or {}
        return OAuthUserInfo(
            provider_user_id=data["id"],
            email=data.get("email"),
            email_verified=data.get("email_confirmed_at") is not None,
            name=user_metadata.get("full_name") or user_metadata.get("name"),
            avatar_url=user_metadata.get("avatar_url"),
        )

    async def _token_request(
        self, *, grant_type: str, payload: dict[str, str]
    ) -> OAuthTokenResult:
        response = await self._request(
            "POST",
            f"/auth/v1/token?grant_type={grant_type}",
            json=payload,
        )
        data = response.json()
        return OAuthTokenResult(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "bearer"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope"),
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["apikey"] = self.anon_key
        headers["Content-Type"] = "application/json"
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout_seconds
            ) as client:
                response = await client.request(method, path, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise OAuthProviderError("Supabase OAuth request failed") from error
