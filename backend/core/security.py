import ast
import redis
import logging
from models.users import Users
from jose import jwt, JWTError
from core.redis import get_redis
from core.config import settings
from core.dependencies import get_db
from sqlalchemy import update, select
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from models.user_sessions import UserSessions
from sqlalchemy.ext.asyncio import AsyncSession
from utils.custom_exception import ServerException
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

async def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    now = datetime.now().astimezone()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def create_password_reset_token(user_id: str, email: str) -> str:
    """Create password reset token"""
    try:
        now = datetime.now().astimezone()
        expire = now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "email": email,
            "token_type": "password_reset",
            "force_change_password": True,
            "iat": now,
            "exp": expire
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return token
        
    except Exception as e:
        raise ServerException(f"Failed to create password reset token: {str(e)}")

async def get_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return credentials.credentials

async def verify_session(sid: str, token: str, redis_client) -> Dict[str, Any]:
    try:
        redis_key = f"session:{sid}"
        raw = await redis_client.get(redis_key)
        if not raw:
            raise ValueError("Invalid or expired session")
        try:
            session_data = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            logger.error(f"Invalid session data: {raw}")
            raise ValueError("Invalid session data")
        
        if session_data.get("access_token") and session_data.get("access_token") != token:
            logger.error(f"Token mismatch: {session_data.get('access_token')} != {token}")
            raise JWTError("Token mismatch")    
        return session_data
    except JWTError as e:
        logger.warning(f"JWT validation failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Failed to verify session: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def verify_token(token: str = Depends(get_token), redis_client = Depends(get_redis), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sid = payload.get("sid")
        if not sid:
            raise ValueError("Missing session ID")
        session_data = await verify_session(sid, token, redis_client)
        
        user = await db.execute(select(Users.status).where(Users.id == payload.get("sub")))
        user_status = user.scalar_one_or_none()
        if user_status is not None and not user_status:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError as e:
        logger.warning(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def verify_password_reset_token(token: str = Depends(get_token)) -> Dict[str, Any]:
    """Verify password reset token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("token_type") != "password_reset":
            raise ValueError("Invalid token type")
        
        # Check if force change password
        if not payload.get("force_change_password"):
            raise ValueError("Token not authorized for password reset")

        if payload.get("exp") < datetime.now().astimezone().timestamp():
            raise ValueError("Token expired")
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise ValueError("Invalid token payload")
        
        return {
            "token": token,
            "sub": user_id,
            "email": email,
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {type(e).__name__}: {str(e)}")        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError as e:
        logger.error(f"Failed to verify password reset token: {str(e)}")        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def extend_session_ttl(redis_client, session_id: str, session_data: Dict[str, Any]) -> None:
    """Extend session TTL and update last activity time"""
    try:
        # Update last activity time using system timezone with timezone info
        session_data["last_activity"] = datetime.now().astimezone().isoformat()
        
        # Reset TTL, start from current time
        ttl = settings.SESSION_EXPIRE_MINUTES * 60
        await redis_client.setex(f"session:{session_id}", ttl, str(session_data))
        
    except Exception as e:
        logger.error(f"Failed to extend session TTL: {e}")


async def clear_user_all_sessions(db: AsyncSession, redis_client: redis.Redis, user_id: str) -> bool:
    """Logout user from all devices by clearing all active sessions"""
    try:
        await db.execute(
            update(UserSessions)
            .where(
                UserSessions.user_id == user_id,
                UserSessions.is_active == True
            )
            .values(is_active=False)
        )
        await db.commit()
        
        result = await db.execute(
            select(UserSessions.id).where(
                UserSessions.user_id == user_id,
                UserSessions.is_active == False
            )
        )
        session_ids = result.scalars().all()
        
        if session_ids:
            redis_keys = [f"session:{sid}" for sid in session_ids]
            await redis_client.delete(*redis_keys)
        
        return True
    except Exception as e:
        raise ServerException(f"Failed to logout all devices: {e}")