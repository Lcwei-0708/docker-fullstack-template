from fastapi import FastAPI
from .cors import add_cors_middleware
from .request_logging import add_request_logging_middleware
from .auth_rate_limiter import add_auth_rate_limiter_middleware


def register_middlewares(app: FastAPI):
    add_cors_middleware(app)
    add_request_logging_middleware(app)
    add_auth_rate_limiter_middleware(app)