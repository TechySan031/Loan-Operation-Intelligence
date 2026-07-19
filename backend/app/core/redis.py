"""
Redis Client — Async Connection

Provides:
- Async Redis connection for pub/sub (nudge delivery)
- Caching for frequent KB queries
- Rate limiting support
- Startup/shutdown lifecycle hooks

Pattern reused from ResearchOS EventBus architecture.
"""

import redis.asyncio as aioredis

from app.config import settings


# --- Global Client ---
redis_client: aioredis.Redis | None = None


async def init_redis():
    """Initialize Redis connection. Called on app startup."""
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    # Verify connection
    await redis_client.ping()


async def close_redis():
    """Close Redis connection. Called on app shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()


def get_redis() -> aioredis.Redis:
    """
    Dependency that provides the Redis client.
    Usage in routes:
        async def my_route(redis: aioredis.Redis = Depends(get_redis)):
    """
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


# --- Pub/Sub Helpers ---
async def publish_nudge(call_id: str, nudge_data: dict):
    """Publish a nudge to the call-specific channel."""
    import json
    channel = f"nudges:{call_id}"
    await redis_client.publish(channel, json.dumps(nudge_data))


async def subscribe_nudges(call_id: str):
    """Subscribe to nudges for a specific call. Returns async generator."""
    pubsub = redis_client.pubsub()
    channel = f"nudges:{call_id}"
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"]
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


# --- Caching Helpers ---
async def cache_get(key: str) -> str | None:
    """Get a cached value."""
    return await redis_client.get(key)


async def cache_set(key: str, value: str, ttl_seconds: int = 300):
    """Set a cached value with TTL."""
    await redis_client.setex(key, ttl_seconds, value)
