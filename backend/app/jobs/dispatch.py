"""Queue background work from the API (spec §5.3 step 14, §5.9).

CELERY_ENABLED=true  -> sent to the Celery worker (task name = registry name).
CELERY_ENABLED=false -> run in this process as an asyncio task (after `countdown` seconds).

`enqueue_debounced` runs a job at most once per window per key ("insights after transaction writes,
debounced 60 s"): the first call schedules it `seconds` later, calls inside the window are dropped.
"""

import asyncio
import logging

from redis.exceptions import RedisError

from app.core.config import settings
from app.core.redis import redis_client

log = logging.getLogger(__name__)

_background: set[asyncio.Task] = set()


async def _run_inline(name: str, args: tuple, countdown: float) -> None:
    from app.jobs.registry import load_all

    try:
        if countdown:
            await asyncio.sleep(countdown)
        await load_all()[name](*args)
    except asyncio.CancelledError:
        raise
    except Exception:
        log.exception("inline job failed", extra={"task": name})


async def enqueue(name: str, *args, countdown: float = 0) -> None:
    args = tuple(str(a) for a in args)  # ids travel as strings (JSON-serializable for Celery)
    if settings.CELERY_ENABLED:
        from app.jobs.celery_app import celery_app

        try:
            await asyncio.to_thread(celery_app.send_task, name, args=list(args), countdown=countdown or None)
            return
        except Exception as exc:  # broker down: don't lose the work
            log.warning("celery unavailable, running inline", extra={"task": name, "error": repr(exc)})
    job = asyncio.create_task(_run_inline(name, args, countdown))
    _background.add(job)
    job.add_done_callback(_background.discard)


async def enqueue_debounced(name: str, key: str, seconds: int) -> bool:
    """Returns True if a run was scheduled, False if one is already pending for this key."""
    try:
        if not await redis_client.set(f"debounce:{name}:{key}", "1", nx=True, ex=seconds):
            return False
    except RedisError:
        pass  # no Redis: schedule anyway
    await enqueue(name, key, countdown=seconds)
    return True


async def drain(timeout: float | None = None) -> None:
    """Wait for in-process jobs (tests, shutdown); after `timeout` seconds the rest are cancelled."""
    loop = asyncio.get_running_loop()
    deadline = None if timeout is None else loop.time() + timeout
    while _background:
        remaining = None if deadline is None else deadline - loop.time()
        if remaining is not None and remaining <= 0:
            for job in list(_background):
                job.cancel()
            await asyncio.gather(*list(_background), return_exceptions=True)
            return
        await asyncio.wait(list(_background), timeout=remaining)
