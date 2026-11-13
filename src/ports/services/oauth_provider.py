from __future__ import annotations

from typing import Protocol

from application.dtos.oauth import OAuthTokenResult, OAuthUserInfo


class OAuthProvider(Protocol):
    async def get_authorization_url(
        self,
        *,
        redirect_uri: str,
        state: str,
        scopes: list[str] | None = None,
    ) -> str: ...

    async def exchange_code(
        self, code: str, *, redirect_uri: str
    ) -> OAuthTokenResult: ...

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResult: ...

    async def get_user_info(self, access_token: str) -> OAuthUserInfo: ...
