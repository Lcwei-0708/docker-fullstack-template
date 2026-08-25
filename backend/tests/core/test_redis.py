from unittest.mock import AsyncMock, patch

import pytest

import core.redis as redis_module
from core.redis import init_redis as real_init_redis


class TestRedis:
    @pytest.mark.asyncio
    async def test_init_redis_sets_global_client(self):
        original = redis_module._redis
        mock_client = object()
        try:
            with patch(
                "core.redis.aioredis.from_url",
                new_callable=AsyncMock,
                return_value=mock_client,
            ) as from_url:
                result = await real_init_redis()
            from_url.assert_awaited_once()
            assert result is mock_client
            assert redis_module.get_redis() is mock_client
        finally:
            redis_module._redis = original
