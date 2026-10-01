"""notifications.* (spec §5.10)."""

from app.core.db import SessionLocal
from app.jobs.registry import task
from app.modules.notifications import reminders
from app.modules.notifications import service as notifications_service


@task("notifications.dispatch")
async def dispatch() -> dict:
    async with SessionLocal() as session:
        return await notifications_service.dispatch_due(session)


@task("notifications.daily_insight")
async def daily_insight() -> int:
    async with SessionLocal() as session:
        return await reminders.daily_insight(session)


@task("notifications.streak_reminder")
async def streak_reminder() -> int:
    async with SessionLocal() as session:
        return await reminders.streak_reminder(session)


@task("notifications.income_reminder")
async def income_reminder() -> int:
    async with SessionLocal() as session:
        return await reminders.income_reminder(session)


@task("notifications.goal_reminder")
async def goal_reminder() -> int:
    async with SessionLocal() as session:
        return await reminders.goal_reminder(session)


@task("notifications.lean_month_alert")
async def lean_month_alert() -> int:
    async with SessionLocal() as session:
        return await reminders.lean_month_alert(session)
