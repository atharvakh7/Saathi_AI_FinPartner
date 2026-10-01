"""schemes.recompute / recompute_all and the translation jobs (spec §5.6, §5.10)."""

import logging
import uuid

from app.core.db import SessionLocal
from app.jobs.registry import task
from app.jobs.tasks_insights import onboarded_user_ids
from app.modules.learn import translate as learn_translate
from app.modules.schemes import service as schemes_service
from app.modules.schemes import translate as schemes_translate

log = logging.getLogger(__name__)


@task("schemes.recompute")
async def recompute(user_id: str) -> dict:
    async with SessionLocal() as session:
        result = await schemes_service.recompute(session, uuid.UUID(user_id))
    await schemes_service.announce_new_matches(uuid.UUID(user_id), result["newly_eligible"])
    return {k: v for k, v in result.items() if k != "newly_eligible"}


@task("schemes.recompute_all")
async def recompute_all() -> int:
    done = 0
    for uid in await onboarded_user_ids():
        try:
            await recompute(str(uid))
            done += 1
        except Exception:
            log.exception("schemes recompute failed", extra={"user_id": str(uid)})
    return done


@task("schemes.translate_missing")
async def translate_schemes() -> int:
    return await schemes_translate.translate_missing()


@task("glossary.translate_missing")
async def translate_glossary() -> dict:
    return await learn_translate.translate_missing()
