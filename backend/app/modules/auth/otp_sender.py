"""Deliver OTP codes (spec §7.4, §8.4 TRAI/DLT).

- console: logs the code (local development only; refused in production by config).
- msg91:   MSG91 OTP API with a DLT-registered template.
"""

import logging

import httpx

from app.core.config import settings
from app.core.errors import AppError
from app.core.pii import mask_phone

log = logging.getLogger(__name__)

MSG91_OTP_URL = "https://control.msg91.com/api/v5/otp"


async def send_otp(phone_e164: str, code: str, expires_in_sec: int) -> None:
    if settings.OTP_PROVIDER == "console":
        # The code goes in its own field so the PII redactor (which masks codes next to
        # the word "otp" in messages) leaves it readable for local testing.
        log.info("otp issued (console provider)", extra={"phone": mask_phone(phone_e164), "dev_otp_code": code})
        return

    params = {
        "template_id": settings.MSG91_TEMPLATE_ID,
        "mobile": phone_e164.lstrip("+"),
        "otp": code,
        "otp_expiry": max(1, expires_in_sec // 60),
    }
    if settings.MSG91_SENDER_ID:
        params["sender"] = settings.MSG91_SENDER_ID
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(MSG91_OTP_URL, params=params, headers={"authkey": settings.MSG91_AUTH_KEY})
        resp.raise_for_status()
        body = resp.json()
        if body.get("type") != "success":
            raise RuntimeError(body.get("message", "unknown MSG91 error"))
    except Exception as exc:
        log.error("otp delivery failed", extra={"phone": mask_phone(phone_e164), "error": str(exc)})
        raise AppError("INTERNAL", "We couldn't send the code. Please try again.") from exc
