import ast
import redis
from typing import Optional
from sqlalchemy import select
from models.users import Users
from core.config import settings
from models.login_logs import LoginLogs
from datetime import datetime, timedelta
from models.user_sessions import UserSessions
from sqlalchemy.ext.asyncio import AsyncSession
from .schema import (
    UserRegister, 
    UserLogin, 
    LoginResult, 
    SessionResult
)
from core.security import (
    verify_password, 
    create_access_token,
    hash_password,
    extend_session_ttl,
    clear_user_all_sessions
)
from utils.custom_exception import (
    ConflictException,
    AuthenticationException,
    ServerException,
    NotFoundException
)

async def register(
    db: AsyncSession, 
    redis_client: redis.Redis,
    user_data: UserRegister, 
    ip_address: str, 
    user_agent: str
) -> LoginResult:
    """User register"""
    user = await _create_user(db, user_data)
    session_result = await _create_user_session(
        db, redis_client, user, ip_address, user_agent
    )
    await _log_login_attempt(
        db, email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        is_success=True,
        user_id=user.id
    )
    return {
        "user": user,
        "session_id": session_result["session_id"],
        "access_token": session_result["access_token"]
    }

async def login(
    db: AsyncSession,
    redis_client: redis.Redis,
    login_data: UserLogin, 
    ip_address: str, 
    user_agent: str
) -> LoginResult:
    """User login"""
    user = await _authenticate_user(db, login_data.email, login_data.password)
    if not user:
        await _log_login_attempt(
            db, email=login_data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            is_success=False,
            failure_reason="Invalid credentials"
        )
        raise AuthenticationException("Invalid email or password")
    
    session_result = await _create_user_session(
        db, redis_client, user, ip_address, user_agent
    )
    await _log_login_attempt(
        db, email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        is_success=True,
        user_id=user.id
    )
    return {
        "user": user,
        "session_id": session_result["session_id"],
        "access_token": session_result["access_token"]
    }

async def logout(
    db: AsyncSession,
    redis_client: redis.Redis,
    user_id: str,
    session_id: str
) -> bool:
    """User logout"""
    try:
        redis_key = f"session:{session_id}"
        await redis_client.delete(redis_key)
        
        result = await db.execute(
            select(UserSessions).where(
                UserSessions.user_id == user_id,
                UserSessions.id == session_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await db.commit()
        
        return True
    except Exception:
        raise ServerException("Logout failed")

async def logout_all_devices(
    db: AsyncSession,
    redis_client: redis.Redis,
    user_id: str
) -> bool:
    """Logout user from all devices"""
    try:
        return await clear_user_all_sessions(db, redis_client, user_id)
    except Exception:
        raise ServerException("Failed to logout all devices")

async def token(
    db: AsyncSession,
    redis_client: redis.Redis,
    session_id: str
) -> str:
    """Use session_id (Cookie) to issue new access_token and refresh session"""
    raw = await redis_client.get(f"session:{session_id}")
    if not raw:
        raise AuthenticationException("Invalid or expired session")
    try:
        data = ast.literal_eval(raw)
    except Exception:
        raise AuthenticationException("Invalid or expired session")

    user_id = data.get("user_id")
    if not user_id:
        raise AuthenticationException("Invalid or expired session")

    # Verify user exists (optional)
    user = await _get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")

    new_access_token = await create_access_token(data={
        "sub": user_id, 
        "email": user.email,
        "sid": session_id
    })
    
    data["access_token"] = new_access_token
    await extend_session_ttl(redis_client, session_id, data)
    await _update_session_expiry(db, session_id)
    
    return new_access_token

async def _update_session_expiry(db: AsyncSession, session_id: str) -> None:
    """Update session expiry time in database"""
    try:
        result = await db.execute(
            select(UserSessions).where(UserSessions.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.expires_at = datetime.now() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
            session.updated_at = datetime.now()
            await db.commit()
    except Exception as e:
        raise ServerException(f"Failed to update session expiry in database: {e}")

async def _create_user(db: AsyncSession, user_data: UserRegister) -> Users:
    try:
        result = await db.execute(
            select(Users).where(Users.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ConflictException("Email already exists")
        
        user = Users(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            hash_password=await hash_password(user_data.password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except ConflictException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to create user: {str(e)}")

async def _authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[Users]:
    result = await db.execute(
        select(Users).where(Users.email == email)
    )
    user = result.scalar_one_or_none()
    if not user or not await verify_password(password, user.hash_password):
        return None
    return user

async def _get_user_by_id(db: AsyncSession, user_id: str) -> Optional[Users]:
    result = await db.execute(
        select(Users).where(Users.id == user_id)
    )
    return result.scalar_one_or_none()

async def _create_user_session(
    db: AsyncSession,
    redis_client: redis.Redis,
    user: Users, 
    ip_address: str, 
    user_agent: str
) -> SessionResult:
    try:
        session = UserSessions(
            user_id=user.id,
            jwt_access_token="",
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        session_id = session.id
        access_token = await create_access_token(data={
            "sub": user.id,
            "email": user.email,
            "sid": session_id
        })

        session.jwt_access_token = access_token
        await db.commit()

        redis_key = f"session:{session_id}"
        session_data = {
            "user_id": user.id,
            "email": user.email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "access_token": access_token,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        await redis_client.setex(
            redis_key, 
            settings.SESSION_EXPIRE_MINUTES * 60,
            str(session_data)
        )
        
        return {
            "session_id": session_id,
            "access_token": access_token
        }
    except Exception as e:
        raise ServerException(f"Failed to create user session: {str(e)}")

async def _log_login_attempt(
    db: AsyncSession,
    email: str, 
    ip_address: str, 
    user_agent: str, 
    is_success: bool, 
    user_id: Optional[str] = None, 
    failure_reason: Optional[str] = None
) -> None:
    log = LoginLogs(
        user_id=user_id,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        is_success=is_success,
        failure_reason=failure_reason
    )
    db.add(log)
    await db.commit()