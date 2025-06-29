from fastapi import APIRouter
from core.config import settings
from .users.controller import router as users_router

api_router = APIRouter()

if settings.DEBUG:
    from .debug.controller import router as debug_router
    api_router.include_router(debug_router, prefix="/debug")

# Add new API modules below.
api_router.include_router(users_router, prefix="/users")