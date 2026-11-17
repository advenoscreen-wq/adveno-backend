"""Unit tests for local Supabase JWT validation."""

import base64
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from application.exceptions.authentication import AuthenticationRequiredError
from config.settings import Settings
from drivers.core.access_token import decode_access_token_user_id

SUPABASE_URL = "https://project.example.supabase.co"
KEY_ID = "test-signing-key"


def create_token(
    private_key: ec.EllipticCurvePrivateKey,
    *,
    subject: str,
    expires_at: datetime,
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": subject,
            "aud": "authenticated",
            "iss": f"{SUPABASE_URL}/auth/v1",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        },
        private_key,
        algorithm="ES256",
        headers={"kid": KEY_ID},
    )


def create_settings(public_key: ec.EllipticCurvePublicKey) -> Settings:
    public_numbers = public_key.public_numbers()

    def encode_coordinate(coordinate: int) -> str:
        return base64.urlsafe_b64encode(coordinate.to_bytes(32, "big")).rstrip(b"=").decode()

    return Settings.model_construct(
        environment="test",
        supabase_url=SUPABASE_URL,
        supabase_jwt_kid=KEY_ID,
        supabase_jwt_x=encode_coordinate(public_numbers.x),
        supabase_jwt_y=encode_coordinate(public_numbers.y),
    )


def test_decode_access_token_returns_subject_after_signature_and_claim_validation() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    subject = uuid4()
    token = create_token(
        private_key,
        subject=str(subject),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )

    user_id = decode_access_token_user_id(
        token,
        create_settings(private_key.public_key()),
    )

    assert user_id == subject


def test_decode_access_token_rejects_invalid_signature() -> None:
    signer = ec.generate_private_key(ec.SECP256R1())
    unrelated_key = ec.generate_private_key(ec.SECP256R1())
    token = create_token(
        signer,
        subject=str(uuid4()),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )

    with pytest.raises(AuthenticationRequiredError):
        decode_access_token_user_id(token, create_settings(unrelated_key.public_key()))


def test_decode_access_token_rejects_expired_token() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    token = create_token(
        private_key,
        subject=str(uuid4()),
        expires_at=datetime.now(UTC) - timedelta(seconds=5),
    )

    with pytest.raises(AuthenticationRequiredError):
        decode_access_token_user_id(token, create_settings(private_key.public_key()))


def test_decode_access_token_rejects_unknown_key_id() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": f"{SUPABASE_URL}/auth/v1",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="ES256",
        headers={"kid": "unexpected-key"},
    )

    with pytest.raises(AuthenticationRequiredError):
        decode_access_token_user_id(token, create_settings(private_key.public_key()))
