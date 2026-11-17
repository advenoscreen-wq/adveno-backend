"""Redis integration coverage for the application cache adapter."""

import pytest

from adapters.services.redis_cache_service import RedisCacheService


@pytest.mark.integration
async def test_redis_cache_set(redis_service: RedisCacheService) -> None:
    await redis_service.set("set-key", "value", ttl_seconds=60)

    assert await redis_service.get("set-key") == "value"


@pytest.mark.integration
async def test_redis_cache_get_missing_value(redis_service: RedisCacheService) -> None:
    assert await redis_service.get("missing-key") is None


@pytest.mark.integration
async def test_redis_cache_delete(redis_service: RedisCacheService) -> None:
    await redis_service.set("delete-key", "value", ttl_seconds=60)

    await redis_service.delete("delete-key")

    assert await redis_service.get("delete-key") is None


@pytest.mark.integration
async def test_redis_cache_pop_consumes_value_once(redis_service: RedisCacheService) -> None:
    await redis_service.set("pop-key", "value", ttl_seconds=60)

    assert await redis_service.pop("pop-key") == "value"
    assert await redis_service.pop("pop-key") is None
