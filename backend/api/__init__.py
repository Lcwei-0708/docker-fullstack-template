from fastapi import APIRouter
from core.config import settings
from .auth.controller import router as auth_router
from .account.controller import router as account_router
from .users.controller import router as users_router
from .roles.controller import router as roles_router

api_router = APIRouter()

if settings.DEBUG_MODE:
    from .debug.controller import router as debug_router
    api_router.include_router(debug_router, prefix="/debug")

# Add new API modules below.
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(account_router, prefix="/account")
api_router.include_router(users_router, prefix="/users")
api_router.include_router(roles_router, prefix="/roles")