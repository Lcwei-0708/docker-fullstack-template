import logging
from utils import get_real_ip
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api_logger")

HEALTH_CHECK_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        client_ip = get_real_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Skip logging for health check and docs
        if path not in HEALTH_CHECK_PATHS:
            logger.info(f"API Request: method={method} path={path} ipAddress={client_ip} user-agent=\"{user_agent}\"")

        response = await call_next(request)

        if path not in HEALTH_CHECK_PATHS:
            logger.info(f"API Response: method={method} path={path} ipAddress={client_ip} user-agent=\"{user_agent}\" status_code={response.status_code}")

        return response

def add_request_logging_middleware(app: FastAPI):
    app.add_middleware(RequestLoggingMiddleware)