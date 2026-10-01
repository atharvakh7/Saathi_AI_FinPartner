"""Shared plumbing for AI adapters: error types and bounded thread offloading.

Every adapter degrades gracefully (spec §10 master prompt rule 6): if its model, binary or
server is missing it raises `AIUnavailable` (or returns None where the spec says so), and
callers turn that into the specified error state or fallback.
"""

import asyncio
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class AIUnavailable(Exception):
    """The dependency is not configured, not installed, or not reachable."""


class AIOutputError(Exception):
    """The model answered, but the output is unusable (e.g. invalid JSON). `raw_text` keeps the answer."""

    def __init__(self, message: str, raw_text: str | None = None) -> None:
        super().__init__(message)
        self.raw_text = raw_text


# One semaphore per (event loop, name): FastAPI and each Celery task run their own loops.
_limiters: dict[tuple[int, str], asyncio.Semaphore] = {}


def limiter(name: str, limit: int) -> asyncio.Semaphore:
    """`async with limiter(...)` bounds concurrent calls within the current event loop."""
    key = (id(asyncio.get_running_loop()), name)
    sem = _limiters.get(key)
    if sem is None:
        sem = _limiters[key] = asyncio.Semaphore(max(1, limit))
    return sem


async def run_blocking(name: str, limit: int, fn: Callable[..., T], *args, **kwargs) -> T:
    """Run a CPU-bound call in a worker thread, at most `limit` at a time per process loop."""
    async with limiter(name, limit):
        return await asyncio.to_thread(fn, *args, **kwargs)

