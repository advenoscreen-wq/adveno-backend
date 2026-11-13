"""Redis implementation of the application cache port."""

from typing import cast

from redis.asyncio import Redis


class RedisCacheService:
    def __init__(self, redis_url: str, *, key_prefix: str = "adveno:") -> None:
        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self._key_prefix = key_prefix

    def _key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        await self._redis.set(self._key(key), value, ex=ttl_seconds)

    async def get(self, key: str) -> str | None:
        return cast(str | None, await self._redis.get(self._key(key)))

    async def delete(self, key: str) -> None:
        await self._redis.delete(self._key(key))

    async def pop(self, key: str) -> str | None:
        return cast(str | None, await self._redis.getdel(self._key(key)))

    async def close(self) -> None:
        await self._redis.aclose()

    async def clear(self) -> None:
        await self._redis.flushdb()
