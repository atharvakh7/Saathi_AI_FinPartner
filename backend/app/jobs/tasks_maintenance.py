"""maintenance.purge (spec §5.10, daily 04:00 IST)."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import delete, or_

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.storage import s3_client
from app.jobs.registry import task
from app.modules.auth.models import OtpRequest, RefreshToken
from app.modules.fraud.models import FraudCheck
from app.modules.users.models import User

log = logging.getLogger(__name__)

OTP_KEEP = timedelta(days=1)
REFRESH_KEEP = timedelta(days=7)
FRAUD_KEEP = timedelta(days=180)
TTS_KEEP = timedelta(days=30)
DELETED_ACCOUNT_KEEP = timedelta(days=30)


def _purge_tts_sync(cutoff: datetime) -> int:
    s3 = s3_client()
    removed = 0
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=settings.S3_BUCKET_TTS, Prefix="tts/"):
        old = [{"Key": o["Key"]} for o in page.get("Contents", []) if o["LastModified"] < cutoff]
        for i in range(0, len(old), 1000):
            s3.delete_objects(Bucket=settings.S3_BUCKET_TTS, Delete={"Objects": old[i:i + 1000], "Quiet": True})
        removed += len(old)
    return removed


@task("maintenance.purge")
async def purge(now: str | None = None) -> dict[str, int]:
    """`now` (ISO) only for tests."""
    now_dt = datetime.fromisoformat(now) if now else datetime.now(timezone.utc)
    out: dict[str, int] = {}
    async with SessionLocal() as session:
        out["otp_requests"] = (await session.execute(
            delete(OtpRequest).where(OtpRequest.expires_at < now_dt - OTP_KEEP))).rowcount
        out["refresh_tokens"] = (await session.execute(delete(RefreshToken).where(or_(
            RefreshToken.expires_at < now_dt - REFRESH_KEEP,
            RefreshToken.revoked_at < now_dt - REFRESH_KEEP,
        )))).rowcount
        out["fraud_checks"] = (await session.execute(
            delete(FraudCheck).where(FraudCheck.created_at < now_dt - FRAUD_KEEP))).rowcount
        # Accounts deleted by the user (DELETE /me): hard delete after 30 days; CASCADE removes their data.
        out["accounts"] = (await session.execute(delete(User).where(
            User.status == "deleted", User.deleted_at < now_dt - DELETED_ACCOUNT_KEEP))).rowcount
        await session.commit()
    try:
        out["tts_objects"] = await asyncio.to_thread(_purge_tts_sync, now_dt - TTS_KEEP)
    except (BotoCoreError, ClientError) as exc:
        log.warning("tts cache purge skipped", extra={"error": repr(exc)})
        out["tts_objects"] = -1
    log.info("maintenance.purge done", extra=out)
    return out
