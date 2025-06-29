import pytest
import asyncio
import pytest_asyncio
import fastapi_limiter
from main import app
from core.config import settings
from core.dependencies import get_db
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from core.database import Base, make_async_url
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

mock_redis = AsyncMock()
mock_redis.evalsha.return_value = 1000  # Indicates 1000ms remaining

async def fake_http_callback(request, response, pexpire):
    return

async def fake_identifier(request):
    return "test"

fastapi_limiter.FastAPILimiter.redis = mock_redis
fastapi_limiter.FastAPILimiter.prefix = "fastapi-limiter"
fastapi_limiter.FastAPILimiter.lua_sha = "dummy_sha"
fastapi_limiter.FastAPILimiter.identifier = fake_identifier
fastapi_limiter.FastAPILimiter.http_callback = fake_http_callback


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """
    Create an isolated database engine for each test.
    Uses optimized connection settings for testing.
    """
    engine = create_async_engine(
        make_async_url(settings.DATABASE_URL_TEST),
        echo=False,
        future=True,
        poolclass=StaticPool,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "charset": "utf8mb4",
            "autocommit": False,
        }
    )
    
    # Create all tables for testing
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup: drop all tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine):
    """
    Create an isolated database session for each test.
    Automatically handles transaction rollback after each test.
    """
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )
    
    async with TestSessionLocal() as session:
        # Start a transaction that will be rolled back after the test
        transaction = await session.begin()
        try:
            yield session
        finally:
            try:
                if transaction.is_active:
                    await transaction.rollback()
            except Exception:
                pass


@pytest_asyncio.fixture
async def client(test_db_session):
    """
    Create a test HTTP client with database dependency override.
    Ensures each test uses its isolated database session.
    """
    
    async def override_get_db():
        yield test_db_session
    
    # Apply the dependency override
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Create HTTP client using ASGI transport
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, 
            base_url="http://testserver",
            timeout=30.0
        ) as ac:
            yield ac
    finally:
        # Always clean up dependency overrides
        app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop():
    """
    Create a session-scoped event loop for pytest-asyncio.
    This resolves event loop conflicts between httpx AsyncClient and database engine.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_other_components():
    """Mock startup components that are not needed for testing"""
    with patch("schedule.register_schedules"), \
         patch("schedule.scheduler.start"), \
         patch("schedule.scheduler.shutdown"), \
         patch("core.redis.init_redis", new=AsyncMock()), \
         patch("core.config.setup_logging"), \
         patch("core.redis.get_redis", return_value=MagicMock()):
        yield


# Mock RateLimiter to always allow requests
@pytest.fixture(autouse=True)
def mock_rate_limiter():
    """Mock RateLimiter to always allow requests"""    
    class MockRateLimiter:
        def __init__(self, *args, **kwargs):
            pass        
        
        def __call__(self, *args, **kwargs):
            return None
            
    with patch("fastapi_limiter.depends.RateLimiter", MockRateLimiter):
        yield


# Optional: Add database utility fixtures for advanced testing scenarios
@pytest_asyncio.fixture
async def db_transaction(test_db_session):
    """
    Provide explicit transaction control for tests that need it.
    Useful for testing transaction-specific behavior.
    """
    transaction = await test_db_session.begin()
    try:
        yield transaction
    finally:
        try:
            if transaction.is_active:
                await transaction.rollback()
        except Exception:
            pass