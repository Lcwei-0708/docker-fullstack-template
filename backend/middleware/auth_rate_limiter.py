import logging
from utils import get_real_ip
from core.redis import get_redis
from core.config import settings
from fastapi import Request, status
from utils.response import APIResponse
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

FAIL_LIMIT = settings.FAIL_LIMIT
FAIL_WINDOW_SECONDS = settings.FAIL_WINDOW_SECONDS
BLOCK_TIME_SECONDS = settings.BLOCK_TIME_SECONDS
HEALTH_CHECK_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}

class AuthRateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        if path in HEALTH_CHECK_PATHS:
            return await call_next(request)
        
        try:
            ip = get_real_ip(request)
            
            redis = get_redis()
            api_block_key = f"block:api:{ip}:{path}"
            
            is_api_blocked = await redis.get(api_block_key)
            if is_api_blocked:
                logger.warning(f"IP {ip} is blocked for API {path}")
                response_data = APIResponse[None](
                    code=429,
                    message="Too many failed attempts. Try again later."
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=response_data.model_dump(exclude_none=True)
                )
            
            response = await call_next(request)
            
            if response.status_code not in (401, 403):
                try:
                    api_fail_key = f"fail:api:{ip}:{path}"
                    await redis.delete(api_fail_key)
                    logger.info(f"IP {ip} API {path} success, cleared fail count")
                except Exception as e:
                    logger.error(f"Failed to clear fail count for IP {ip} on API {path}: {e}")
            
            if response.status_code in (401, 403):
                try:
                    api_fail_key = f"fail:api:{ip}:{path}"
                    api_fails = await redis.incr(api_fail_key)
                    logger.info(f"IP {ip} API {path} fail count: {api_fails}")
                    
                    if api_fails == 1:
                        await redis.expire(api_fail_key, FAIL_WINDOW_SECONDS)
                    
                    if api_fails >= FAIL_LIMIT:
                        logger.warning(f"IP {ip} is now blocked for API {path} for {BLOCK_TIME_SECONDS} seconds")
                        await redis.set(api_block_key, 1, ex=BLOCK_TIME_SECONDS)
                        await redis.delete(api_fail_key)
                        
                except Exception as e:
                    logger.error(f"Rate limiter error for IP {ip} on API {path}: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"Unexpected error in rate limiter middleware for path {path}: {e}")
            return await call_next(request)

def add_auth_rate_limiter_middleware(app):
    app.add_middleware(AuthRateLimiterMiddleware)