from fastapi import APIRouter
from .debug.controller import router as debug_router
from .users.controller import router as users_router

api_router = APIRouter()

# Add new API modules below.
api_router.include_router(debug_router, prefix="/debug")
api_router.include_router(users_router, prefix="/users")