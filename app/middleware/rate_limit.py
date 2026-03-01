"""In-memory sliding-window rate limiter middleware."""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.middleware.request_id import request_id_var


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._request_count = 0

    def _client_key(self, request: Request) -> str:
        """Key by API key hash (from Authorization header) or client IP."""
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            return f"key:{auth[7:][:16]}"
        client = request.client
        return f"ip:{client.host}" if client else "ip:unknown"

    async def dispatch(self, request: Request, call_next):
        now = time.monotonic()
        window = 60.0
        limit = settings.api_rate_limit_per_minute
        key = self._client_key(request)

        # Prune expired timestamps for this key
        timestamps = self._hits[key]
        cutoff = now - window
        self._hits[key] = [t for t in timestamps if t > cutoff]
        timestamps = self._hits[key]

        if len(timestamps) >= limit:
            retry_after = int(timestamps[0] - cutoff) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "status": 429,
                    "request_id": request_id_var.get(""),
                },
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)

        # Periodic cleanup of stale keys every 100 requests
        self._request_count += 1
        if self._request_count % 100 == 0:
            stale_keys = [k for k, v in self._hits.items() if not v or v[-1] < cutoff]
            for k in stale_keys:
                del self._hits[k]

        return await call_next(request)
