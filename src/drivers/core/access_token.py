"""Local verification of Supabase access tokens."""

from uuid import UUID

import jwt
from jwt.exceptions import PyJWTError

from application.exceptions.authentication import AuthenticationRequiredError
from config.settings import Settings


def decode_access_token_user_id(access_token: str, settings: Settings) -> UUID:
    """Verify the Supabase JWT signature and claims, then return its subject UUID."""
    if not all((settings.supabase_jwt_kid, settings.supabase_jwt_x, settings.supabase_jwt_y)):
        raise AuthenticationRequiredError()

    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
    try:
        header = jwt.get_unverified_header(access_token)
        if (
            header.get("alg") != settings.supabase_jwt_algorithm
            or header.get("kid") != settings.supabase_jwt_kid
        ):
            raise AuthenticationRequiredError()
        public_key = jwt.PyJWK.from_dict(
            {
                "kty": "EC",
                "crv": "P-256",
                "alg": settings.supabase_jwt_algorithm,
                "kid": settings.supabase_jwt_kid,
                "x": settings.supabase_jwt_x,
                "y": settings.supabase_jwt_y,
            }
        ).key
        claims = jwt.decode(
            access_token,
            key=public_key,
            algorithms=[settings.supabase_jwt_algorithm],
            audience="authenticated",
            issuer=issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
        subject = claims["sub"]
        if not isinstance(subject, str):
            raise AuthenticationRequiredError()
        return UUID(subject)
    except (PyJWTError, KeyError, TypeError, ValueError) as error:
        raise AuthenticationRequiredError() from error
