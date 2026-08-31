from core.config import settings, setup_logging

setup_logging("logging_config.yaml")
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import api_router
from core.database import init_db
from core.redis import init_redis
from core.telemetry import setup_telemetry, shutdown_telemetry
from extensions import register_extensions
from middleware import register_middlewares
from schedule import register_schedules, scheduler


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    register_schedules()
    scheduler.start()
    await init_redis()
    yield
    scheduler.shutdown()
    shutdown_telemetry()


# Control docs exposure by environment variable DEBUG_MODE
docs_url = "/" if settings.DEBUG_MODE else None
redoc_url = "/redoc" if settings.DEBUG_MODE else None
openapi_url = "/openapi.json" if settings.DEBUG_MODE else None

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

# Register all extensions
register_extensions(app)

# Register all middlewares
register_middlewares(app)

# Register all API routes with a global prefix '/api'
app.include_router(api_router, prefix="/api")


# Health check endpoint
@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"status": "ok"}


setup_telemetry(app)
