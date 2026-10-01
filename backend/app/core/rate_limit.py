"""Redis sliding-window rate limiter (spec §7.4 limits, §8.3).

- `hit()` is the primitive.
- `rate_limit(name, limit, window_sec, scope)` builds a FastAPI dependency for
  per-endpoint limits, e.g. `Depends(rate_limit("chat_messages", 30, 60))`.
- Global per-user / per-IP limits are enforced by `RateLimitMiddleware` in middleware.py.

If Redis is unreachable the limiter fails open (logs a warning) so an outage of the
cache does not take the API down.
"""

import logging
import time
import uuid

from fastapi import Request
from redis.exceptions import RedisError

from app.core.errors import AppError
from app.core.redis import redis_client

log = logging.getLogger(__name__)

# KEYS[1] = zset key; ARGV = now_ms, window_ms, limit, member
# Returns 0 when allowed, otherwise milliseconds until the oldest entry leaves the window.
_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count < limit then
  redis.call('ZADD', key, now, ARGV[4])
  redis.call('PEXPIRE', key, window)
  return 0
end
local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
local retry = window - (now - tonumber(oldest[2]))
if retry < 1 then retry = 1 end
return retry
"""

_script = redis_client.register_script(_SLIDING_WINDOW_LUA)


async def hit(key: str, limit: int, window_sec: int) -> int | None:
    """Record one request. Returns Retry-After seconds if over the limit, else None."""
    now_ms = int(time.time() * 1000)
    try:
        retry_ms = await _script(
            keys=[f"rl:{key}"],
            args=[now_ms, window_sec * 1000, limit, f"{now_ms}-{uuid.uuid4().hex[:8]}"],
        )
    except RedisError as exc:
        log.warning("rate limiter unavailable, allowing request", extra={"error": str(exc)})
        return None
    if int(retry_ms) == 0:
        return None
    return max(1, -(-int(retry_ms) // 1000))  # ceil to whole seconds


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limited_error(retry_after: int) -> AppError:
    return AppError(
        "RATE_LIMITED",
        details={"retry_after_sec": retry_after},
        headers={"Retry-After": str(retry_after)},
    )


def rate_limit(name: str, limit: int, window_sec: int, scope: str = "user"):
    """Per-endpoint limit dependency. scope='user' falls back to IP when unauthenticated."""

    async def _dependency(request: Request) -> None:
        user_id = getattr(request.state, "user_id", None)
        subject = f"u:{user_id}" if scope == "user" and user_id else f"ip:{client_ip(request)}"
        retry_after = await hit(f"{name}:{subject}", limit, window_sec)
        if retry_after is not None:
            raise rate_limited_error(retry_after)

    return _dependency
