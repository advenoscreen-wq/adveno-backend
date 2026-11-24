"""Redis implementation of the application cache port."""

import logging
from collections.abc import Awaitable
from typing import TypeVar, cast

from redis.asyncio import Redis

logger = logging.getLogger(__name__)
T = TypeVar("T")


class RedisCacheService:
    def __init__(self, redis_url: str, *, key_prefix: str = "adveno:") -> None:
        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self._key_prefix = key_prefix

    def _key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    async def _execute(self, operation: str, result: Awaitable[T]) -> T:
        try:
            value = await result
        except Exception as error:
            logger.error(
                "Redis operation failed",
                extra={"operation": operation, "error_type": type(error).__name__},
            )
            raise
        logger.info("Redis operation completed", extra={"operation": operation})
        return value

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        await self._execute("set", self._redis.set(self._key(key), value, ex=ttl_seconds))

    async def get(self, key: str) -> str | None:
        return cast(str | None, await self._execute("get", self._redis.get(self._key(key))))

    async def delete(self, key: str) -> None:
        await self._execute("delete", self._redis.delete(self._key(key)))

    async def pop(self, key: str) -> str | None:
        return cast(str | None, await self._execute("pop", self._redis.getdel(self._key(key))))

    async def increment_with_ttl(self, key: str, *, ttl_seconds: int) -> int:
        script = (
            "local count = redis.call('INCR', KEYS[1]); "
            "if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]); end; "
            "return count"
        )
        result = await self._execute(
            "increment_with_ttl",
            self._redis.eval(script, 1, self._key(key), ttl_seconds),
        )
        return int(result)

    async def close(self) -> None:
        await self._execute("close", self._redis.aclose())

    async def clear(self) -> None:
        await self._execute("clear", self._redis.flushdb())
