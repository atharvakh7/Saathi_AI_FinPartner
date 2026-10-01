"""Celery app and beat schedule (spec §5.9–5.10, times in IST).

    .venv/Scripts/celery -A app.jobs.celery_app worker --pool=solo -l info   # Windows needs --pool=solo
    .venv/Scripts/celery -A app.jobs.celery_app beat -l info

Every registry job becomes a Celery task of the same name. Task bodies are async; each worker
process keeps ONE event loop for its lifetime, so the async DB/Redis pools (bound to the loop they
were created on) stay valid across tasks.
"""

import asyncio
import logging

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init

from app.core.config import settings
from app.core.logging import configure_logging
from app.jobs.registry import load_all

log = logging.getLogger(__name__)

celery_app = Celery("saathi", broker=settings.CELERY_BROKER_URL)
celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_ignore_result=True,
    task_acks_late=True,            # a crashed worker's task is redelivered
    worker_prefetch_multiplier=1,   # LLM jobs are slow; don't hoard them
    task_time_limit=30 * 60,
    broker_connection_retry_on_startup=True,
)

_loop: asyncio.AbstractEventLoop | None = None


def run(coro):
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop.run_until_complete(coro)


@worker_process_init.connect
def _fresh_loop(**_):
    """Forked worker children must not reuse the parent's loop or pooled connections."""
    global _loop
    _loop = None


def _make_task(name, fn):
    @celery_app.task(name=name)
    def _task(*args):
        return run(fn(*args))

    return _task


configure_logging()
for _name, _fn in load_all().items():
    _make_task(_name, _fn)

celery_app.conf.beat_schedule = {
    "insights-daily": {"task": "insights.generate_all", "schedule": crontab(hour=8, minute=30)},
    # per-user times: checked every 15 min against each user's chosen time
    "daily-insight-push": {"task": "notifications.daily_insight", "schedule": crontab(minute="*/15")},
    "streak-reminder": {"task": "notifications.streak_reminder", "schedule": crontab(minute="*/15")},
    "income-reminder": {"task": "notifications.income_reminder", "schedule": crontab(day_of_week="sun", hour=18, minute=0)},
    "goal-reminder": {"task": "notifications.goal_reminder", "schedule": crontab(day_of_month=1, hour=10, minute=0)},
    "lean-month-alert": {"task": "notifications.lean_month_alert", "schedule": crontab(day_of_month=1, hour=9, minute=0)},
    "push-dispatch": {"task": "notifications.dispatch", "schedule": crontab(minute="*")},
    "planner-nightly": {"task": "planner.regenerate_all", "schedule": crontab(hour=2, minute=0)},
    "schemes-nightly": {"task": "schemes.recompute_all", "schedule": crontab(hour=3, minute=30)},
    "maintenance-purge": {"task": "maintenance.purge", "schedule": crontab(hour=4, minute=0)},
}
