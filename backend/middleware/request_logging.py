import logging
import time
from utils import get_real_ip
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.config import SKIP_METHODS, SKIP_PATHS
from core.config import settings
from utils.log_sanitize import (
    format_log_value,
    sanitize_body,
    sanitize_query,
    should_omit_body,
)

logger = logging.getLogger("api_logger")

_BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _append_field(extra: str, name: str, value: str) -> str:
    if not value:
        return extra
    return f"{extra} {name}={format_log_value(value)}"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        client_ip = get_real_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        if path in SKIP_PATHS or method in SKIP_METHODS:
            return await call_next(request)

        request_extra = ""
        if settings.LOG_HTTP_BODY:
            request_extra = _append_field(
                request_extra, "query", sanitize_query(request.query_params)
            )
            if method in _BODY_METHODS:
                raw = await request.body()
                request_extra = _append_field(
                    request_extra,
                    "payload",
                    sanitize_body(
                        raw,
                        request.headers.get("content-type", ""),
                        settings.LOG_HTTP_BODY_MAX_BYTES,
                    ),
                )

        logger.info(
            f"API Request: method={method} path={path} ipAddress={client_ip} "
            f"user-agent=\"{user_agent}\"{request_extra}"
        )

        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000

        response_extra = ""
        if settings.LOG_HTTP_BODY:
            content_type = response.headers.get("content-type", "")
            if should_omit_body(content_type):
                response_extra = _append_field(response_extra, "data", "[omitted]")
            else:
                body = b"".join([chunk async for chunk in response.body_iterator])
                response_extra = _append_field(
                    response_extra,
                    "data",
                    sanitize_body(
                        body,
                        content_type,
                        settings.LOG_HTTP_BODY_MAX_BYTES,
                    ),
                )
                # Replay on the same response so multiple Set-Cookie headers stay intact.
                # dict(response.headers) collapses them into one and drops csrf_token.
                async def _replay(content: bytes = body):
                    yield content

                response.body_iterator = _replay()

        logger.info(
            f"API Response: method={method} path={path} ipAddress={client_ip} "
            f"status_code={response.status_code} duration={duration_ms:.1f}ms "
            f"user-agent=\"{user_agent}\"{response_extra}"
        )

        return response


def add_request_logging_middleware(app: FastAPI):
    app.add_middleware(RequestLoggingMiddleware)
