import pytest
import asyncio
import pytest_asyncio
import fastapi_limiter
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from core.config import settings
from core.database import Base, make_async_url
from core.dependencies import get_db
from core.redis import get_redis
from core.security import create_access_token, hash_password
from main import app
from models.password_reset_tokens import PasswordResetTokens
from models.user_sessions import UserSessions
from models.users import Users
from models.roles import Roles
from models.role_attributes import RoleAttributes
from models.role_attributes_mapper import RoleAttributesMapper
from models.role_mapper import RoleMapper

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



@pytest_asyncio.fixture(scope="function")
async def account_test_user(test_db_session: AsyncSession):
    """Create a dedicated test user for account module tests"""
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
    """Create authentication headers for account module tests"""
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

# Users module specific fixtures
@pytest_asyncio.fixture(scope="function")
async def users_test_user(test_db_session: AsyncSession):
    """Create test user for users API tests"""
    user_id = str(uuid4())
    hashed_pwd = await hash_password("UsersTestPassword123!")

    user = Users(
        id=user_id,
        email="userstest@example.com",
        first_name="Users",
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
async def users_test_role(test_db_session: AsyncSession):
    """Create admin role for users API tests"""
    role_id = str(uuid4())
    role = Roles(
        id=role_id,
        name="admin",
        description="Administrator role with full permissions"
    )
    test_db_session.add(role)
    await test_db_session.commit()
    await test_db_session.refresh(role)
    return role


@pytest_asyncio.fixture(scope="function")
async def users_test_role_attributes(test_db_session: AsyncSession, users_test_role: Roles):
    """Create role attributes and mappings for users management permissions"""
    
    view_users_attr = RoleAttributes(
        id=str(uuid4()),
        name="view-users"
    )
    manage_users_attr = RoleAttributes(
        id=str(uuid4()),
        name="manage-users"
    )
    
    test_db_session.add(view_users_attr)
    test_db_session.add(manage_users_attr)
    await test_db_session.commit()
    
    attribute_mappings = [
        RoleAttributesMapper(
            role_id=users_test_role.id,
            attributes_id=view_users_attr.id,
            value=True
        ),
        RoleAttributesMapper(
            role_id=users_test_role.id,
            attributes_id=manage_users_attr.id,
            value=True
        )
    ]
    
    for mapping in attribute_mappings:
        test_db_session.add(mapping)
    
    await test_db_session.commit()
    return attribute_mappings


@pytest_asyncio.fixture(scope="function")
async def users_test_role_mapping(test_db_session: AsyncSession, users_test_user: Users, users_test_role: Roles):
    """Create role mapping for test user"""    
    role_mapping = RoleMapper(
        user_id=users_test_user.id,
        role_id=users_test_role.id
    )
    
    test_db_session.add(role_mapping)
    await test_db_session.commit()
    return role_mapping


@pytest_asyncio.fixture(scope="function")
async def users_test_session(test_db_session: AsyncSession, users_test_user: Users):
    """Create a test user session for users API tests"""
    session_id = str(uuid4())
    access_token = await create_access_token(
        {
            "sub": users_test_user.id,
            "sid": session_id,
            "email": users_test_user.email,
        }
    )

    user_session = UserSessions(
        id=session_id,
        user_id=users_test_user.id,
        jwt_access_token=access_token,
        ip_address="127.0.0.1",
        user_agent="UsersTestAgent/1.0",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        expires_at=datetime.now() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES),
    )

    test_db_session.add(user_session)
    await test_db_session.commit()
    await test_db_session.refresh(user_session)

    return user_session


@pytest_asyncio.fixture(scope="function")
async def users_auth_headers(
    users_test_user: Users, 
    users_test_session: UserSessions, 
    users_test_role_mapping,
    users_test_role_attributes
):
    """Generate authentication headers for users API tests"""
    session_data = {
        "sid": users_test_session.id,
        "user_id": users_test_user.id,
        "email": users_test_user.email,
        "access_token": users_test_session.jwt_access_token,
        "created_at": users_test_session.created_at.isoformat(),
        "last_activity": datetime.now().isoformat(),
        "expires_at": users_test_session.expires_at.isoformat(),
    }

    session_key = f"session:{users_test_session.id}"

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
        "Authorization": f"Bearer {users_test_session.jwt_access_token}",
        "session_data": session_data,
        "session_id": users_test_session.id,
        "access_token": users_test_session.jwt_access_token,
    }


# Auth module specific fixtures
@pytest_asyncio.fixture
async def create_password_reset_token_with_invalid_user(test_db_session: AsyncSession):
    """Create a password reset token with invalid user for testing edge cases"""
    
    nonexistent_user_id = "nonexistent_user_id"
    token_id = str(uuid4())
    token_string = "test_token_123"
    expires_at = datetime.now() + timedelta(minutes=30)
    
    # Temporarily disable foreign key checks to insert invalid data
    await test_db_session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    await test_db_session.execute(text("""
        INSERT INTO password_reset_tokens (id, user_id, token, is_used, expires_at, created_at, updated_at)
        VALUES (:id, :user_id, :token, :is_used, :expires_at, NOW(), NOW())
    """), {
        "id": token_id,
        "user_id": nonexistent_user_id,
        "token": token_string,
        "is_used": False,
        "expires_at": expires_at
    })
    # Re-enable foreign key checks
    await test_db_session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    await test_db_session.commit()
    
    return {
        "token_id": token_id,
        "user_id": nonexistent_user_id,
        "token": token_string,
        "expires_at": expires_at,
        "token_data": {
            "sub": nonexistent_user_id,
            "token": token_string
        }
    }


@pytest_asyncio.fixture
async def create_password_reset_token_with_valid_user(test_db_session: AsyncSession):
    """Create a password reset token with valid user for testing normal scenarios"""
    user_id = str(uuid4())
    hashed_pwd = await hash_password("TestPassword123!")
    
    user = Users(
        id=user_id,
        email="tokenuser@example.com",
        first_name="Token",
        last_name="User",
        phone="+1234567890",
        hash_password=hashed_pwd,
        status=True,
        password_reset_required=True
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    token_id = str(uuid4())
    token_string = "valid_test_token_123"
    expires_at = datetime.now() + timedelta(minutes=30)
    
    reset_token_record = PasswordResetTokens(
        id=token_id,
        user_id=user_id,
        token=token_string,
        is_used=False,
        expires_at=expires_at
    )
    test_db_session.add(reset_token_record)
    await test_db_session.commit()
    
    return {
        "token_id": token_id,
        "user_id": user_id,
        "token": token_string,
        "expires_at": expires_at,
        "user": user,
        "token_record": reset_token_record,
        "token_data": {
            "sub": user_id,
            "token": token_string
        }
    }
