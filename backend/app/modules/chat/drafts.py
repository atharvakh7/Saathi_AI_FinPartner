"""Pending confirmations (spec §5.3 step 7): `draft:{user_id}` in Redis, 10 minutes.

kinds: "transaction" and "goal" wait for yes/no; "goal_needs_amount" keeps the goal text so the
user's next message ("2 lakh in 2 years") can complete it.
"""

import json
import logging
import uuid

from redis.exceptions import RedisError

from app.core.redis import redis_client

log = logging.getLogger(__name__)

DRAFT_TTL_SEC = 600


def _key(user_id: uuid.UUID) -> str:
    return f"draft:{user_id}"


async def save(user_id: uuid.UUID, kind: str, data: dict) -> None:
    try:
        await redis_client.set(_key(user_id), json.dumps({"kind": kind, "data": data}, default=str), ex=DRAFT_TTL_SEC)
    except RedisError as exc:
        log.warning("draft not saved", extra={"error": str(exc)})


async def pop(user_id: uuid.UUID) -> dict | None:
    """Read and remove the pending draft (a draft is answered once)."""
    try:
        raw = await redis_client.getdel(_key(user_id))
    except RedisError as exc:
        log.warning("draft unavailable", extra={"error": str(exc)})
        return None
    return json.loads(raw) if raw else None


async def clear(user_id: uuid.UUID) -> None:
    try:
        await redis_client.delete(_key(user_id))
    except RedisError:
        pass
