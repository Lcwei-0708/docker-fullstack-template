import pytest
import asyncio
from main import app
import pytest_asyncio
import fastapi_limiter
from uuid import uuid4
from models.users import Users
from core.redis import get_redis
from core.config import settings
from core.dependencies import get_db
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from models.user_sessions import UserSessions
from core.database import Base, make_async_url
from core.security import create_access_token, hash_password
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
        },
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
        autocommit=False,
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

    async def override_get_redis():
        return mock_redis

    # Apply the dependency overrides
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    try:
        # Create HTTP client using ASGI transport
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver", timeout=30.0
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
    with patch("schedule.register_schedules"), patch("schedule.scheduler.start"), patch(
        "schedule.scheduler.shutdown"
    ), patch("core.redis.init_redis", new=AsyncMock()), patch(
        "core.config.setup_logging"
    ):
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


# Authentication fixtures for testing
@pytest_asyncio.fixture
async def test_user(test_db_session: AsyncSession):
    """
    Create a test user for authentication tests.
    Automatically creates a user with hashed password in the test database.
    """
    user_id = str(uuid4())
    hashed_pwd = await hash_password("TestPassword123!")

    user = Users(
        id=user_id,
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        phone="+1234567890",
        hash_password=hashed_pwd,
        status=True,
        password_reset_required=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_user_session(test_db_session: AsyncSession, test_user: Users):
    """
    Create a test user session in the database.
    Automatically creates a session record for the test user.
    """
    session_id = str(uuid4())
    access_token = await create_access_token(
        {"sub": test_user.id, "sid": session_id, "email": test_user.email}
    )

    user_session = UserSessions(
        id=session_id,
        user_id=test_user.id,
        jwt_access_token=access_token,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        expires_at=datetime.now() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES),
    )

    test_db_session.add(user_session)
    await test_db_session.commit()
    await test_db_session.refresh(user_session)

    return user_session


@pytest_asyncio.fixture
async def auth_headers(test_user: Users, test_user_session: UserSessions):
    """
    Generate authentication headers with valid token and session data.
    Automatically configures mock Redis with session data for authentication.

    Returns:
        dict: Contains Authorization header and session data for testing
    """
    session_data = {
        "sid": test_user_session.id,
        "user_id": test_user.id,
        "email": test_user.email,
        "access_token": test_user_session.jwt_access_token,
        "created_at": test_user_session.created_at.isoformat(),
        "last_activity": datetime.now().isoformat(),
        "expires_at": test_user_session.expires_at.isoformat(),
    }

    # Configure global mock_redis to return session data for the specific session key
    session_key = f"session:{test_user_session.id}"

    # Configure mock_redis to return session data when called with the session key
    async def mock_get(key):
        if key == session_key:
            return str(session_data)
        return None

    # Set the mock function
    mock_redis.get = mock_get
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True

    return {
        "Authorization": f"Bearer {test_user_session.jwt_access_token}",
        "session_data": session_data,
        "session_id": test_user_session.id,
        "access_token": test_user_session.jwt_access_token,
    }


# Module-specific fixtures for better test organization
@pytest.fixture(scope="function")
def account_module_fixtures():
    """
    Provide account module specific fixtures and utilities.
    This fixture can be used by account module tests for common setup.
    """
    from tests.api.account.test_utils import (
        AccountTestDataFactory,
        AccountTestAssertions,
        AccountTestMocks,
        AccountTestScenarios,
    )

    return {
        "data_factory": AccountTestDataFactory(),
        "assertions": AccountTestAssertions(),
        "mocks": AccountTestMocks(),
        "scenarios": AccountTestScenarios(),
    }


@pytest.fixture(scope="function")
def mock_redis_for_account():
    """
    Provide a mock Redis client specifically configured for account module tests.
    This fixture ensures consistent Redis mocking across account tests.
    """
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    mock_redis.evalsha.return_value = 1000

    return mock_redis


@pytest_asyncio.fixture(scope="function")
async def account_test_user(test_db_session: AsyncSession):
    """
    Create a dedicated test user specifically for account module tests.
    This ensures account tests have a clean, isolated user to work with.
    """
    from uuid import uuid4
    from datetime import datetime
    from core.security import hash_password

    user_id = str(uuid4())
    hashed_pwd = await hash_password("AccountTestPassword123!")

    user = Users(
        id=user_id,
        email="accounttest@example.com",
        first_name="Account",
        last_name="Test",
        phone="+1234567890",
        hash_password=hashed_pwd,
        status=True,
        password_reset_required=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope="function")
async def account_auth_headers(account_test_user: Users, test_db_session: AsyncSession):
    """
    Create authentication headers specifically for account module tests.
    This fixture provides a clean auth setup for account API tests.
    """
    from uuid import uuid4
    from datetime import datetime, timedelta
    from core.security import create_access_token
    from models.user_sessions import UserSessions
    from core.config import settings

    session_id = str(uuid4())
    access_token = await create_access_token(
        {
            "sub": account_test_user.id,
            "sid": session_id,
            "email": account_test_user.email,
        }
    )

    user_session = UserSessions(
        id=session_id,
        user_id=account_test_user.id,
        jwt_access_token=access_token,
        ip_address="127.0.0.1",
        user_agent="AccountTestAgent/1.0",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        expires_at=datetime.now() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES),
    )

    test_db_session.add(user_session)
    await test_db_session.commit()
    await test_db_session.refresh(user_session)

    # Configure mock Redis for this session
    session_data = {
        "sid": user_session.id,
        "user_id": account_test_user.id,
        "email": account_test_user.email,
        "access_token": user_session.jwt_access_token,
        "created_at": user_session.created_at.isoformat(),
        "last_activity": datetime.now().isoformat(),
        "expires_at": user_session.expires_at.isoformat(),
    }

    session_key = f"session:{user_session.id}"

    async def mock_get(key):
        if key == session_key:
            return str(session_data)
        return None

    mock_redis.get = mock_get
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True

    return {
        "Authorization": f"Bearer {user_session.jwt_access_token}",
        "session_data": session_data,
        "session_id": user_session.id,
        "access_token": user_session.jwt_access_token,
    }


# Test configuration fixtures
@pytest.fixture(scope="function")
def account_test_config():
    """
    Provide test configuration specific to account module.
    This fixture can be used to configure test-specific settings.
    """
    return {
        "test_timeout": 30.0,
        "max_retries": 3,
        "test_user_prefix": "account_test_",
        "mock_redis_prefix": "account_test:",
        "test_data_cleanup": True,
    }


# Performance testing fixtures
@pytest.fixture(scope="function")
def account_performance_fixtures():
    """
    Provide fixtures for performance testing in account module.
    This includes timing utilities and performance assertions.
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def measure_time(operation_name: str):
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            print(f"{operation_name} took {duration:.4f} seconds")

    return {
        "measure_time": measure_time,
        "max_acceptable_time": 1.0,  # seconds
        "performance_threshold": 0.5,  # seconds
    }
