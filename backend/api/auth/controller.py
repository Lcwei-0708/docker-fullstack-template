import logging
from core.redis import get_redis
from core.config import settings
from .schema import UserResponse
from core.dependencies import get_db
from core.security import verify_token
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from utils.response import APIResponse, parse_responses, common_responses
from .schema import (
    UserRegister, 
    UserLogin, 
    UserLoginResponse,
    TokenResponse
)
from .services import (
    register,
    login,
    logout,
    token,
    logout_all_devices
)
from utils.custom_exception import (
    ConflictException,
    AuthenticationException,
    NotFoundException
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])

@router.post(
    "/register", 
    response_model=APIResponse[UserLoginResponse], 
    response_model_exclude_none=True,
    summary="Register account",
    responses=parse_responses({
        200: ("User registered successfully", UserLoginResponse),
        409: ("Email already exists", None)
    }, common_responses)
)
async def register_api(
    user_data: UserRegister,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    try:
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "Registration")
        
        result = await register(db, redis_client, user_data, client_ip, user_agent)
        
        user = result["user"]
        session_id = result["session_id"]
        access_token = result["access_token"]
        
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=settings.COOKIE_HTTPONLY,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.SESSION_EXPIRE_MINUTES * 60
        )
        
        user_response = UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone
        )
        
        response_data = UserLoginResponse(
            access_token=access_token,
            expires_at=datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            user=user_response
        )
        return APIResponse(code=200, message="User registered successfully", data=response_data)
    except ConflictException:
        raise HTTPException(status_code=409, detail="Email already exists")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/login", 
    response_model=APIResponse[UserLoginResponse],
    response_model_exclude_none=True,
    summary="Login account",
    responses=parse_responses({
        200: ("User logged in successfully", UserLoginResponse),
        401: ("Invalid email or password", None)
    }, common_responses)
)
async def login_api(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    try:
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        result = await login(db, redis_client, user_data, client_ip, user_agent)
        
        user = result["user"]
        session_id = result["session_id"]
        access_token = result["access_token"]
        
        user_response = UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone
        )
        
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=settings.COOKIE_HTTPONLY,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.SESSION_EXPIRE_MINUTES * 60
        )
        
        response_data = UserLoginResponse(
            access_token=access_token,
            expires_at=datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            user=user_response
        )
        return APIResponse(code=200, message="User logged in successfully", data=response_data)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/logout", 
    response_model=APIResponse[None],
    response_model_exclude_none=True,
    summary="Logout account",
    responses=parse_responses({
        200: ("User logged out successfully", None),
        401: ("Invalid or expired session / Invalid or expired token", None)
    }, common_responses)
)
async def logout_api(
    token: dict = Depends(verify_token),
    response: Response = None,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    try:
        user_id = token.get("sub")
        session_id = token.get("sid")
        
        if not user_id or not session_id:
            raise AuthenticationException("Invalid or expired session")
        
        if await logout(db, redis_client, user_id, session_id):
            if response:
                response.delete_cookie("session_id")
            return APIResponse(code=200, message="User logged out successfully")
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/logout-all", 
    response_model=APIResponse[None],
    response_model_exclude_none=True,
    summary="Logout all devices",
    responses=parse_responses({
        200: ("All devices logged out successfully", None)
    }, common_responses)
)
async def logout_all_api(
    token: dict = Depends(verify_token),
    response: Response = None,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Logout user from all devices"""
    try:
        user_id = token.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        if await logout_all_devices(db, redis_client, user_id):
            if response:
                response.delete_cookie("session_id")
            return APIResponse(code=200, message="All devices logged out successfully")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/token",
    response_model=APIResponse[TokenResponse],
    response_model_exclude_unset=True,
    summary="Refresh token",
    responses=parse_responses({
        200: ("Token refreshed successfully", TokenResponse),
        401: ("Invalid or expired session", None)
    }, common_responses)
)
async def token_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Use session_id Cookie to get new access_token"""
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise AuthenticationException("Invalid or expired session")
        new_access_token = await token(db, redis_client, session_id)
        response_data = TokenResponse(
            access_token=new_access_token,
            expires_at=datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return APIResponse(code=200, message="Token refreshed successfully", data=response_data)
    except (AuthenticationException, NotFoundException):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    except Exception:
        raise HTTPException(status_code=500)