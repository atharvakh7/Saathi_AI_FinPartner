"""Auth request/response bodies (spec §7.4)."""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.schemas import UserOut

PHONE_PATTERN = r"^\+91[6-9]\d{9}$"


class OtpRequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_e164: str = Field(pattern=PHONE_PATTERN)


class OtpRequestOut(BaseModel):
    request_id: uuid.UUID
    expires_in_sec: int
    resend_after_sec: int


class OtpVerifyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_e164: str = Field(pattern=PHONE_PATTERN)
    code: str = Field(pattern=r"^\d{6}$")
    device_id: str | None = Field(default=None, max_length=100)
    platform: Literal["android", "ios"] | None = None


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class OtpVerifyOut(TokenPairOut):
    is_new_user: bool
    user: UserOut


class RefreshIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(min_length=20, max_length=200)


class LogoutIn(RefreshIn):
    pass
