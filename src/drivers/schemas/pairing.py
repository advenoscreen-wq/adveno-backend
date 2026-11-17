"""Schemas for screen pairing endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from domain.value_object import PairingSessionStatus, PairingType


class CreateScreenPairingSessionResponse(BaseModel):
    session_id: UUID
    pairing_token: str
    expires_at: datetime


class CreateScreenPairingSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pairing_type: PairingType


class ApproveScreenPairingSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    screen_id: UUID | None = None


class ScreenPairingSessionStatusResponse(BaseModel):
    status: PairingSessionStatus


class VerifyScreenPairingSessionResponse(BaseModel):
    session_id: UUID
    status: PairingSessionStatus
    pairing_type: PairingType | None
    screen_id: UUID | None
    screen_exists: bool
    expires_at: datetime
    created_at: datetime


class ApproveScreenPairingSessionResponse(BaseModel):
    session_id: UUID
    pairing_type: PairingType
    status: PairingSessionStatus
    screen_id: UUID | None
    paired_at: datetime | None


class CreatePairedScreenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    device_model: str | None = None
    app_version: str | None = None


class CreatePairedScreenResponse(BaseModel):
    screen_id: UUID
    screen_code: str
    name: str
    credential: str


class IssuePairedScreenCredentialResponse(BaseModel):
    screen_id: UUID
    credential: str
