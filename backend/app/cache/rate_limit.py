import logging
import time

import redis

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, client) -> None:
        self.client = client

    def enforce(self, key: str, limit: int, window_seconds: int, fail_closed: bool) -> dict[str, int]:
        bucket = int(time.time()) // window_seconds
        redis_key = f"rl:{key}:{bucket}"
        try:
            count = int(self.client.incr(redis_key))
            if count == 1:
                self.client.expire(redis_key, window_seconds)
            remaining = max(limit - count, 0)
            snapshot = {"limit": limit, "remaining": remaining}
            if count > limit:
                retry_after = self.client.ttl(redis_key)
                raise AppError(
                    429,
                    "RATE_LIMITED",
                    "Too many requests. Try again shortly.",
                    headers={
                        "Retry-After": str(max(int(retry_after), 1)),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )
            return snapshot
        except AppError:
            raise
        except redis.RedisError:
            logger.exception("Rate limiter unavailable for %s", key)
            if fail_closed:
                raise AppError(503, "RATE_LIMIT_UNAVAILABLE", "Rate limiter unavailable")
            return {"limit": limit, "remaining": limit}


def remember_limit(request, snapshot: dict[str, int]) -> None:
    current = getattr(request.state, "rate_limit", None)
    if current is None or snapshot["remaining"] < current["remaining"]:
        request.state.rate_limit = snapshot
