"""Shared async Redis client (rate limits, OTP throttling, caches, drafts)."""

from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
    health_check_interval=30,
)


def get_redis() -> Redis:
    return redis_client
