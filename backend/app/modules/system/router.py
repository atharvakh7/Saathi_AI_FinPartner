"""GET /health — liveness plus dependency status (spec §7.4)."""

import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.ai import classifier, llm_client, ocr, stt, tts
from app.core.db import engine
from app.core.redis import redis_client

log = logging.getLogger(__name__)
router = APIRouter(tags=["system"])

CHECK_TIMEOUT_SEC = 2.5


class HealthOut(BaseModel):
    status: str
    db: bool
    redis: bool
    llm: bool
    stt: bool
    tts: bool
    ocr: bool
    classifier: bool


async def _check_db() -> bool:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True


async def _check_redis() -> bool:
    return bool(await redis_client.ping())


async def _safe(name: str, coro) -> bool:
    try:
        return bool(await asyncio.wait_for(coro, timeout=CHECK_TIMEOUT_SEC))
    except Exception as exc:  # any failure = unavailable
        log.warning("health check failed", extra={"dependency": name, "error": repr(exc)})
        return False


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    db, redis_ok, llm, stt_ok = await asyncio.gather(
        _safe("db", _check_db()),
        _safe("redis", _check_redis()),
        _safe("llm", llm_client.is_available()),
        _safe("stt", stt.check_available()),
    )
    return HealthOut(
        # Liveness: always 200. "degraded" when a core store (db/redis) is down.
        status="ok" if db and redis_ok else "degraded",
        db=db,
        redis=redis_ok,
        llm=llm,
        stt=stt_ok,
        tts=tts.is_available(),
        ocr=ocr.is_available(),
        classifier=classifier.is_available(),
    )
