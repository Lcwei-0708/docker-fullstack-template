import redis.asyncio as aioredis
from core.config import settings

_redis = None

async def init_redis():
    global _redis
    _redis = await aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    return _redis

def get_redis():
    return _redis