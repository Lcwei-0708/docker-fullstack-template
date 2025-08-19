from core.config import settings, setup_logging
setup_logging("logging_config.yaml")
from api import api_router
from fastapi import FastAPI
from core.redis import init_redis, get_redis
from core.database import init_db
from fastapi_limiter import FastAPILimiter
from contextlib import asynccontextmanager
from extensions import register_extensions
from middleware import register_middlewares
from fastapi.responses import RedirectResponse
from schedule import scheduler, register_schedules

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    register_schedules()
    scheduler.start()
    await init_redis()
    await FastAPILimiter.init(get_redis())
    yield
    scheduler.shutdown()

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

# Register all extensions
register_extensions(app)

# Register all middlewares
register_middlewares(app)

# Register all API routes with a global prefix '/api'
app.include_router(api_router, prefix="/api")

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")