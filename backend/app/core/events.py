"""In-process domain events: modules announce changes, later modules react.

    @on(PROFILE_UPDATED)
    async def recompute_schemes(user_id): ...

    await emit(PROFILE_UPDATED, user.id)

Handlers run after the change is committed. A failing handler is logged and never fails the
user's request. Background-job handlers (Celery, step 17) should enqueue quickly here.
"""

import logging
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable

log = logging.getLogger(__name__)

Handler = Callable[[uuid.UUID], Awaitable[None]]

PROFILE_UPDATED = "profile_updated"
ONBOARDING_COMPLETED = "onboarding_completed"
TRANSACTIONS_CHANGED = "transactions_changed"
DEBTS_CHANGED = "debts_changed"
GOALS_CHANGED = "goals_changed"

_handlers: dict[str, list[Handler]] = defaultdict(list)


def on(event: str) -> Callable[[Handler], Handler]:
    def register(handler: Handler) -> Handler:
        _handlers[event].append(handler)
        return handler

    return register


async def emit(event: str, user_id: uuid.UUID) -> None:
    handlers = _handlers.get(event, [])
    log.info("event", extra={"event": event, "user_id": str(user_id), "handlers": len(handlers)})
    for handler in handlers:
        try:
            await handler(user_id)
        except Exception:
            log.exception("event handler failed", extra={"event": event, "handler": handler.__name__})
