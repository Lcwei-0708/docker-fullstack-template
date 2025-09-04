from fastapi import APIRouter
from core.config import settings
from .auth.controller import router as auth_router
from .user.controller import router as user_router

api_router = APIRouter()

if settings.DEBUG:
    from .debug.controller import router as debug_router
    api_router.include_router(debug_router, prefix="/debug")

# Add new API modules below.
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(user_router, prefix="/user")