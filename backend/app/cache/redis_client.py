import json
import logging

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

VERSION_KEY = "cache:services:version"


class RedisStore:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
        return self._client

    def ping(self) -> bool:
        return bool(self.client.ping())

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def get(self, key: str) -> str | None:
        return self.client.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.client.set(key, value, ex=ex)

    def delete(self, *keys: str) -> None:
        if keys:
            self.client.delete(*keys)

    def incr(self, key: str) -> int:
        return int(self.client.incr(key))

    def expire(self, key: str, seconds: int) -> None:
        self.client.expire(key, seconds)

    def ttl(self, key: str) -> int:
        return int(self.client.ttl(key))

    def get_json(self, key: str):
        try:
            raw = self.get(key)
        except redis.RedisError:
            logger.exception("Redis read failed for %s", key)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Discarding unreadable cache entry %s", key)
            return None

    def set_json(self, key: str, value, ttl: int) -> None:
        try:
            self.set(key, json.dumps(value), ex=ttl)
        except redis.RedisError:
            logger.exception("Redis write failed for %s", key)

    def version(self) -> int | None:
        try:
            raw = self.get(VERSION_KEY)
            return int(raw) if raw else 1
        except redis.RedisError:
            logger.exception("Redis version read failed")
            return None

    def bump_version(self) -> None:
        try:
            self.incr(VERSION_KEY)
        except redis.RedisError:
            logger.exception("Redis cache invalidation failed")

    def delete_pattern(self, pattern: str) -> None:
        try:
            keys = list(self.client.scan_iter(match=pattern, count=200))
            if keys:
                self.client.delete(*keys)
        except redis.RedisError:
            logger.exception("Redis delete pattern failed for %s", pattern)


store = RedisStore()
