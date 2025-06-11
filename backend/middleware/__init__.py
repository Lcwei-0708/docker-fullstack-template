from fastapi import FastAPI
from .cors import add_cors_middleware

def register_middlewares(app: FastAPI):
    # Add new middleware imports below.
    add_cors_middleware(app)