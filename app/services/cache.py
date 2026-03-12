"""Simple async-aware in-memory TTL cache.

Single-process friendly (no Redis needed). Stores values in a dict
with expiry timestamps. Stale entries are lazily evicted on read.
"""

import asyncio
import time

_cache: dict[str, tuple[object, float]] = {}
_locks: dict[str, asyncio.Lock] = {}


async def cached(key: str, ttl_seconds: int, fetch_fn):
    """Return cached value if fresh, otherwise call *fetch_fn* and store result."""
    now = time.monotonic()
    entry = _cache.get(key)
    if entry is not None:
        value, expires_at = entry
        if now < expires_at:
            return value

    # Serialize concurrent calls for the same key so only one fetches
    if key not in _locks:
        _locks[key] = asyncio.Lock()

    async with _locks[key]:
        # Double-check after acquiring lock
        entry = _cache.get(key)
        if entry is not None:
            value, expires_at = entry
            if now < expires_at:
                return value

        value = await fetch_fn()
        _cache[key] = (value, time.monotonic() + ttl_seconds)
        return value


def invalidate(key: str) -> None:
    """Remove a specific cache entry."""
    _cache.pop(key, None)
