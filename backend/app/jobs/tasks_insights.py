"""insights.generate_all / insights.generate_user / planner.regenerate_all (spec §5.9–5.10)."""

import logging
import uuid

from sqlalchemy import select

from app.core.db import SessionLocal
from app.jobs.registry import task
from app.modules.insights import service as insights_service
from app.modules.planner import service as planner_service
from app.modules.users.models import User, UserProfile

log = logging.getLogger(__name__)


async def onboarded_user_ids() -> list[uuid.UUID]:
    async with SessionLocal() as session:
        return list((await session.execute(
            select(User.id).join(UserProfile, UserProfile.user_id == User.id)
            .where(User.status == "active", UserProfile.onboarding_completed_at.is_not(None))
        )).scalars())


@task("insights.generate_user")
async def generate_user(user_id: str) -> int:
    async with SessionLocal() as session:
        return len(await insights_service.generate_for_user(session, uuid.UUID(user_id)))


@task("insights.scheme_news")
async def scheme_news(user_id: str, scheme_ids: str) -> bool:
    """I09 after a recompute found newly eligible schemes (ids comma-separated)."""
    async with SessionLocal() as session:
        ids = [uuid.UUID(i) for i in scheme_ids.split(",") if i]
        return await insights_service.scheme_news(session, uuid.UUID(user_id), ids) is not None


@task("insights.generate_all")
async def generate_all() -> int:
    total = 0
    for uid in await onboarded_user_ids():
        try:
            total += await generate_user(str(uid))
        except Exception:
            log.exception("insights failed for a user", extra={"user_id": str(uid)})
    log.info("insights.generate_all done", extra={"insights_created": total})
    return total


@task("planner.regenerate_all")
async def regenerate_all() -> int:
    done = 0
    for uid in await onboarded_user_ids():
        try:
            async with SessionLocal() as session:
                await planner_service.regenerate(session, uid)
            done += 1
        except Exception:
            log.exception("planner regenerate failed", extra={"user_id": str(uid)})
    log.info("planner.regenerate_all done", extra={"users": done})
    return done
