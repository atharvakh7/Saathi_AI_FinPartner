"""User-level events (spec §7.4): thin wrappers over app.core.events.

PUT /me/profile -> profile_updated (scheme recompute, planner regenerate: steps 10, 13, 17).
First POST /me/onboarding-complete -> onboarding_completed (first planner/risk/insight run).
"""

import uuid

from app.core import events
from app.core.events import Handler


def on_profile_updated(handler: Handler) -> Handler:
    return events.on(events.PROFILE_UPDATED)(handler)


def on_onboarding_completed(handler: Handler) -> Handler:
    return events.on(events.ONBOARDING_COMPLETED)(handler)


async def profile_updated(user_id: uuid.UUID) -> None:
    await events.emit(events.PROFILE_UPDATED, user_id)


async def onboarding_completed(user_id: uuid.UUID) -> None:
    await events.emit(events.ONBOARDING_COMPLETED, user_id)
