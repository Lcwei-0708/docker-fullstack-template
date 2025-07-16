from fastapi import FastAPI
from .cors import add_cors_middleware
from .request_logging import add_request_logging_middleware


def register_middlewares(app: FastAPI):
    # Add new middleware imports below.
    add_cors_middleware(app)
    add_request_logging_middleware(app)