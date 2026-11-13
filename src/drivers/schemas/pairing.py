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
