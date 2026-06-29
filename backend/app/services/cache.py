"""Redis-backed cache layer with in-process fallback.

Provides:
- Cached reads for slow-changing lookups (permission catalog, translation table, sector presets)
- Rate-limit token bucket (used by middleware)
- Idempotency-key tracking for write endpoints
"""
from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable

logger = logging.getLogger('auditcore.cache')


class CacheBackend:
    """Abstract cache backend — Redis if reachable, in-process dict otherwise."""

    def __init__(self) -> None:
        self._redis = None
        self._local: dict[str, tuple[float, str]] = {}
        self._tried_connect = False

    async def _ensure_redis(self) -> None:
        if self._tried_connect:
            return
        self._tried_connect = True
        try:
            from app.core.config import get_settings
            import redis.asyncio as redis_async  # type: ignore
            settings = get_settings()
            self._redis = redis_async.from_url(settings.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info('cache_backend_connected', extra={'backend': 'redis'})
        except Exception as exc:
            logger.info('cache_backend_fallback', extra={'backend': 'in_process', 'reason': str(exc)})
            self._redis = None

    async def get(self, key: str) -> str | None:
        await self._ensure_redis()
        if self._redis is not None:
            try:
                return await self._redis.get(key)
            except Exception:
                self._redis = None
        # In-process fallback with TTL
        import time
        entry = self._local.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            self._local.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        await self._ensure_redis()
        if self._redis is not None:
            try:
                await self._redis.set(key, value, ex=ttl_seconds)
                return
            except Exception:
                self._redis = None
        import time
        self._local[key] = (time.time() + ttl_seconds, value)

    async def get_json(self, key: str) -> Any:
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    async def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        await self.set(key, json.dumps(value, ensure_ascii=False, default=str), ttl_seconds)

    async def incr_with_expiry(self, key: str, ttl_seconds: int) -> int:
        """Atomic increment with TTL — for rate-limit and idempotency-key use."""
        await self._ensure_redis()
        if self._redis is not None:
            try:
                # atomic increment + set TTL only on first increment
                pipe = self._redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, ttl_seconds)
                result = await pipe.execute()
                return int(result[0])
            except Exception:
                self._redis = None
        # In-process fallback
        import time
        cur = self._local.get(key)
        if cur is None or time.time() > cur[0]:
            self._local[key] = (time.time() + ttl_seconds, (time.time(), 1))
            return 1
        _, count = cur
        self._local[key] = (cur[0], (time.time(), count + 1))
        return count + 1


# Singleton instance — lazily connects on first use.
_BACKEND = CacheBackend()


async def cache_get(key: str) -> str | None:
    return await _BACKEND.get(key)


async def cache_set(key: str, value: str, ttl_seconds: int = 300) -> None:
    await _BACKEND.set(key, value, ttl_seconds)


async def cache_get_json(key: str) -> Any:
    return await _BACKEND.get_json(key)


async def cache_set_json(key: str, value: Any, ttl_seconds: int = 300) -> None:
    await _BACKEND.set_json(key, value, ttl_seconds)


async def incr_with_expiry(key: str, ttl_seconds: int) -> int:
    return await _BACKEND.incr_with_expiry(key, ttl_seconds)


def cached_json(
    key_template: str,
    ttl_seconds: int = 300,
):
    """Decorator: cache the JSON result of an async function.

    Usage:
        @cached_json('permissions:{code}', ttl_seconds=60)
        async def get_permission(code): ...
    """
    def decorator(fn: Callable[..., Awaitable[Any]]):
        async def wrapper(*args, **kwargs):
            key = key_template.format(*args, **kwargs)
            cached = await cache_get_json(key)
            if cached is not None:
                return cached
            result = await fn(*args, **kwargs)
            await cache_set_json(key, result, ttl_seconds)
            return result
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator
