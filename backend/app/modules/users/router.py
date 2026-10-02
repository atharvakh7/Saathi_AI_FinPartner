"""/me/* and /legal/* endpoints (spec §7.2, §7.4)."""

import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import AppError
from app.core.i18n import resolve_language
from app.core.rate_limit import rate_limit
from app.core.security import get_current_user
from app.modules.users import service
from app.modules.users.export import build_export
from app.modules.users.models import User
from app.modules.users.schemas import (
    ConfidenceIn,
    ConfidenceOut,
    ConsentOut,
    ConsentsIn,
    DeleteMeIn,
    DeviceTokenIn,
    DeviceTokenOut,
    MeOut,
    MePatchIn,
    NotificationSettingsIn,
    NotificationSettingsOut,
    PrivacyNoticeOut,
    ProfileIn,
    ProfileOut,
    UserOut,
)

router = APIRouter(prefix="/me", tags=["users"])
legal_router = APIRouter(prefix="/legal", tags=["legal"])

LEGAL_DIR = Path(__file__).resolve().parents[2] / "seed" / "legal"


# --- /me -------------------------------------------------------------------------

@router.get("", response_model=MeOut)
async def get_me(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    profile = await service.get_profile(session, user)
    return MeOut(
        user=service.to_user_out(user, profile),
        profile=ProfileOut.model_validate(profile) if profile else None,
        needs=await service.next_onboarding_step(session, user, profile),
    )


@router.patch("", response_model=UserOut)
async def patch_me(body: MePatchIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    if body.preferred_language is not None:
        user.preferred_language = body.preferred_language
    profile = await service.ensure_profile(session, user)
    if body.voice_reply_enabled is not None:
        profile.voice_reply_enabled = body.voice_reply_enabled
    await session.commit()
    return service.to_user_out(user, profile)


@router.delete("", status_code=202)
async def delete_me(body: DeleteMeIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    if body.confirm != "DELETE":
        raise AppError("VALIDATION_ERROR", details=[{"field": "confirm", "issue": 'must be exactly "DELETE"'}])
    await service.schedule_account_deletion(session, user)
    return {"status": "scheduled"}


# --- Profile & onboarding --------------------------------------------------------

@router.get("/profile", response_model=ProfileOut)
async def get_profile(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    profile = await service.get_profile(session, user)
    if profile is None:
        raise AppError("NOT_FOUND")
    return profile


@router.put("/profile", response_model=ProfileOut)
async def put_profile(body: ProfileIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.update_profile(session, user, body)


@router.post("/confidence-assessment", response_model=ConfidenceOut)
async def confidence_assessment(
    body: ConfidenceIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return await service.submit_confidence(session, user, body)


@router.post("/onboarding-complete", response_model=UserOut)
async def onboarding_complete(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    profile = await service.complete_onboarding(session, user)
    return service.to_user_out(user, profile)


# --- Consents --------------------------------------------------------------------

@router.get("/consents", response_model=list[ConsentOut])
async def get_consents(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return service.consents_out(await service.current_consents(session, user.id))


@router.post("/consents", response_model=list[ConsentOut])
async def post_consents(body: ConsentsIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.record_consents(session, user, body)


# --- Device tokens ---------------------------------------------------------------

@router.post("/device-tokens", response_model=DeviceTokenOut, status_code=201)
async def post_device_token(
    body: DeviceTokenIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return DeviceTokenOut(id=await service.register_device_token(session, user, body.expo_push_token, body.platform))


@router.delete("/device-tokens/{token_id}", status_code=204)
async def delete_device_token(
    token_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.delete_device_token(session, user, token_id)
    return Response(status_code=204)


# --- Notification settings -------------------------------------------------------

@router.get("/notification-settings", response_model=NotificationSettingsOut)
async def get_notification_settings(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.get_notification_settings(session, user)


@router.put("/notification-settings", response_model=NotificationSettingsOut)
async def put_notification_settings(
    body: NotificationSettingsIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return await service.update_notification_settings(session, user, body)


# --- Export ----------------------------------------------------------------------

@router.get("/export", dependencies=[Depends(rate_limit("me_export", 5, 3600))])
async def export_me(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    data = await build_export(session, user)
    filename = f"saathi-data-{datetime.now(timezone.utc):%Y%m%d}.json"
    return JSONResponse(data, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# --- Legal (public) --------------------------------------------------------------

@lru_cache
def _privacy_template(language: str) -> str:
    return (LEGAL_DIR / f"privacy_{language}.md").read_text(encoding="utf-8")


@legal_router.get("/privacy-notice", response_model=PrivacyNoticeOut)
async def privacy_notice(request: Request, lang: str | None = None):
    language = resolve_language(request, lang)
    markdown = (
        _privacy_template(language)
        .replace("{{VERSION}}", service.PRIVACY_NOTICE_VERSION)
        .replace("{{GRIEVANCE_EMAIL}}", settings.GRIEVANCE_EMAIL)
    )
    return PrivacyNoticeOut(version=service.PRIVACY_NOTICE_VERSION, language=language, markdown=markdown)
