import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import SKIP_METHODS, SKIP_PATHS, settings
from core.redis import get_redis
from utils import get_real_ip
from utils.response import APIResponse

logger = logging.getLogger("rate_limiter")

RATE_LIMIT = settings.RATE_LIMIT
RATE_LIMIT_WINDOW_SECONDS = settings.RATE_LIMIT_WINDOW_SECONDS
BLOCK_TIME_SECONDS = settings.BLOCK_TIME_SECONDS


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.whitelist_ips = settings.rate_limit_whitelist_ips
        self.endpoint_rate_limits = {}
        self._configure_endpoint_limits()

    def _configure_endpoint_limits(self):
        """
        Configure rate limits for specific endpoints.
        Only endpoints listed here will override the default rate limit settings.

        Format:
            {
                "path": {
                    "limit": (count, window_seconds) or None,
                    # (allowed_requests, time_window) or None to disable rate limiting
                    "status_codes": [int, ...],  # Optional: count only these status codes
                    "clear_on_success": bool  # Optional: clear counter on 2xx responses
                }
            }
        """
        self.endpoint_rate_limits = {
            # Add endpoint rate limits here to override default settings
            "/api/auth/token": {"limit": (60, 60), "status_codes": None, "clear_on_success": False},
            "/api/auth/login": {
                "limit": (5, 30),
                "status_codes": [401, 403],
                "clear_on_success": True,
            },
            "/api/roles/permissions": {
                "limit": (60, 60),
                "status_codes": None,
                "clear_on_success": False,
            },
            "/api/debug/test-ip": {
                "limit": (10, 60),
                "status_codes": None,
                "clear_on_success": False,
            },
        }

    def _get_rate_limit_config(self, path: str) -> dict:
        """
        Get rate limit configuration for a path.
        Returns custom config if exists, otherwise returns default config.
        """
        custom_config = self.endpoint_rate_limits.get(path)
        if custom_config:
            return custom_config

        # Default configuration for all endpoints
        return {
            "limit": (RATE_LIMIT, RATE_LIMIT_WINDOW_SECONDS),
            "status_codes": None,
            "clear_on_success": False,
        }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        if path in SKIP_PATHS or method in SKIP_METHODS:
            return await call_next(request)

        response = None
        try:
            ip = get_real_ip(request)
            if self.whitelist_ips and ip in self.whitelist_ips:
                return await call_next(request)

            redis = get_redis()
            if redis is None:
                return await call_next(request)

            # Get rate limit config
            rate_limit_config = self._get_rate_limit_config(path)

            # If limit is None, skip rate limiting for this endpoint
            if rate_limit_config.get("limit") is None:
                return await call_next(request)

            api_block_key = f"block:api:{ip}:{path}"

            # Check if IP is blocked for this endpoint
            is_blocked = await redis.get(api_block_key)
            if is_blocked:
                resp = APIResponse[None](code=429, message="Too many requests. Try again later.")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=resp.model_dump(exclude_none=True),
                )

            response = await call_next(request)
            status_codes = rate_limit_config.get("status_codes")
            limit_count, window_seconds = rate_limit_config["limit"]
            clear_on_success = rate_limit_config.get("clear_on_success", False)
            is_success = 200 <= response.status_code < 300

            should_count = False
            if not status_codes:
                should_count = True
            elif status_codes and response.status_code in status_codes:
                should_count = True

            if should_count:
                try:
                    api_fail_key = f"fail:api:{ip}:{path}"
                    api_fails = await redis.incr(api_fail_key)

                    if api_fails == 1:
                        await redis.expire(api_fail_key, window_seconds)

                    if api_fails >= limit_count:
                        await redis.set(api_block_key, 1, ex=BLOCK_TIME_SECONDS)
                        await redis.delete(api_fail_key)
                        resp = APIResponse[None](
                            code=429, message="Too many requests. Try again later."
                        )
                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content=resp.model_dump(exclude_none=True),
                        )
                except Exception as e:
                    logger.error(
                        f"Rate limiter error: method={method} path={path} error={e} ipAddress={ip}"
                    )
            elif clear_on_success and is_success:
                try:
                    api_fail_key = f"fail:api:{ip}:{path}"
                    await redis.delete(api_fail_key)
                except Exception as e:
                    logger.error(
                        f"Failed to clear count: method={method} path={path} "
                        f"error={e} ipAddress={ip}"
                    )

            return response

        except Exception as e:
            logger.error(f"Unexpected error in rate limiter middleware for path {path}: {e}")
            if response is not None:
                return response
            return await call_next(request)


def add_rate_limiter_middleware(app):
    app.add_middleware(RateLimiterMiddleware)
