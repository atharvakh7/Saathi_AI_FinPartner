"""/auth/* endpoints (spec §7.2, §7.4)."""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rate_limit import client_ip
from app.core.security import get_current_user
from app.modules.auth import service
from app.modules.auth.schemas import (
    LogoutIn,
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    OtpVerifyOut,
    RefreshIn,
    TokenPairOut,
)
from app.modules.users.models import User
from app.modules.users.service import get_profile, to_user_out

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/request", response_model=OtpRequestOut)
async def otp_request(body: OtpRequestIn, request: Request, session: AsyncSession = Depends(get_db)):
    otp = await service.request_otp(session, body.phone_e164, client_ip(request))
    return OtpRequestOut(
        request_id=otp.id, expires_in_sec=service.OTP_TTL_SEC, resend_after_sec=service.OTP_RESEND_AFTER_SEC
    )


@router.post("/otp/verify", response_model=OtpVerifyOut)
async def otp_verify(body: OtpVerifyIn, session: AsyncSession = Depends(get_db)):
    user, is_new, access, refresh, expires_in = await service.verify_otp(
        session, body.phone_e164, body.code, body.device_id
    )
    profile = await get_profile(session, user)
    return OtpVerifyOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=expires_in,
        is_new_user=is_new,
        user=to_user_out(user, profile),
    )


@router.post("/token/refresh", response_model=TokenPairOut)
async def token_refresh(body: RefreshIn, session: AsyncSession = Depends(get_db)):
    access, refresh, expires_in = await service.refresh_tokens(session, body.refresh_token)
    return TokenPairOut(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/logout", status_code=204)
async def logout(
    body: LogoutIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.logout(session, user, body.refresh_token)
    return Response(status_code=204)
