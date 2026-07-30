import logging
from core.redis import get_redis
from core.config import settings
from .schema import UserResponse
from core.dependencies import get_db
from datetime import datetime, timedelta
from utils.get_real_ip import get_real_ip
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import verify_password_reset_token, verify_token, verify_email_verification_token
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from utils.response import APIResponse, parse_responses, common_responses, make_error_examples
from extensions.smtp import get_mailer, SMTPMailer
from utils.custom_exception import SMTPNotConfiguredException
from .schema import (
    UserRegister, 
    UserLogin, 
    UserLoginResponse,
    TokenResponse,
    CsrfTokenResponse,
    ResetPasswordRequest,
    TokenValidationResponse,
    LogoutRequest,
    ForgotPasswordRequest,
    PasswordResetCooldownResponse,
    ResendVerificationRequest,
    ActionRequiredResponse,
    action_required_response_examples
)
from .services import (
    register,
    login,
    logout,
    token,
    logout_all_devices,
    reset_password,
    validate_password_reset_token,
    forgot_password,
    get_password_reset_cooldown,
    verify_email,
    resend_verification_email,
    get_or_create_csrf_token,
    verify_csrf_token,
)
from utils.custom_exception import (
    ConflictException,
    AuthenticationException,
    PasswordResetRequiredException,
    NotFoundException,
    ValidationException,
    EmailVerificationRequiredException,
    RegistrationDisabledException,
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
        202: ("Email verification required", None),
        409: ("Email already exists", None),
        503: ("Registration is disabled", None)
    }, common_responses)
)
async def register_api(
    user_data: UserRegister,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
    mailer: SMTPMailer = Depends(get_mailer)
):
    try:
        client_ip = get_real_ip(request)
        user_agent = request.headers.get("user-agent", "Registration")
        
        result = await register(db, redis_client, user_data, client_ip, user_agent, mailer)
        
        user = result["user"]
        session_id = result["session_id"]
        access_token = result["access_token"]
        csrf_token = result["csrf_token"]

        _set_session_cookie(response, session_id)
        _set_csrf_cookie(response, csrf_token)
        
        user_response = UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone
        )
        
        response_data = UserLoginResponse(
            access_token=access_token,
            expires_at=datetime.now().astimezone() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            user=user_response
        )
        return APIResponse(code=200, message="User registered successfully", data=response_data)
    except EmailVerificationRequiredException as e:
        resp = APIResponse(code=202, message="Email verification required")
        raise HTTPException(status_code=202, detail=resp.dict(exclude_none=True))
    except ConflictException:
        raise HTTPException(status_code=409, detail="Email already exists")
    except RegistrationDisabledException:
        raise HTTPException(status_code=503, detail="Registration is disabled")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/login", 
    response_model=APIResponse[UserLoginResponse],
    response_model_exclude_none=True,
    summary="Login account",
    responses=parse_responses({
        200: ("User logged in successfully", UserLoginResponse),
        202: ("Action required", ActionRequiredResponse, action_required_response_examples),
        401: ("Invalid email or password", None)
    }, common_responses)
)
async def login_api(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
    mailer: SMTPMailer = Depends(get_mailer)
):
    try:
        client_ip = get_real_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        result = await login(db, redis_client, user_data, client_ip, user_agent, mailer)
        
        user = result["user"]
        session_id = result["session_id"]
        access_token = result["access_token"]
        csrf_token = result["csrf_token"]

        user_response = UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone
        )

        _set_session_cookie(response, session_id)
        _set_csrf_cookie(response, csrf_token)
        
        response_data = UserLoginResponse(
            access_token=access_token,
            expires_at=datetime.now().astimezone() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            user=user_response
        )
        return APIResponse(code=200, message="User logged in successfully", data=response_data)
    except PasswordResetRequiredException as e:
        resp = APIResponse(code=202, message="Password reset required", data=e.details)
        raise HTTPException(status_code=202, detail=resp.dict(exclude_none=True))
    except EmailVerificationRequiredException as e:
        resp = APIResponse(code=202, message="Email verification required", data=e.details)
        raise HTTPException(status_code=202, detail=resp.dict(exclude_none=True))
    except AuthenticationException as e:
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
        401: ("Unauthorized", None, make_error_examples(401, {
            "invalidSession": "Invalid or expired session",
            "invalidToken": "Invalid or expired token",
        })),
    }, common_responses)
)
async def logout_api(
    logout_data: LogoutRequest,
    token: dict = Depends(verify_token),
    response: Response = None,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """
    Logout user from current device or all devices
    
    Args:
        logout_data: Contains logout_all flag to determine logout scope
    """
    try:
        user_id = token.get("sub")
        session_id = token.get("sid")
        
        if logout_data.logout_all:
            # Logout from all devices
            if await logout_all_devices(db, redis_client, user_id):
                if response:
                    _clear_auth_cookies(response)
                return APIResponse(code=200, message="User logged out successfully")
        else:
            # Logout from current device only
            if not session_id:
                raise AuthenticationException("Invalid or expired session")
            
            if await logout(db, redis_client, user_id, session_id):
                if response:
                    _clear_auth_cookies(response)
                return APIResponse(code=200, message="User logged out successfully")
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/token",
    response_model=APIResponse[TokenResponse],
    response_model_exclude_unset=True,
    summary="Refresh token",
    responses=parse_responses({
        200: ("Token refreshed successfully", TokenResponse),
        401: ("Unauthorized", None, make_error_examples(401, {
            "invalidSession": "Invalid or expired session",
            "invalidCsrf": "Invalid or expired CSRF token",
        })),
    }, common_responses)
)
async def token_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Validate CSRF token then use session_id cookie to issue new access_token"""
    try:
        csrf_token = request.headers.get("X-CSRF-Token")
        sid_from_csrf = await verify_csrf_token(redis_client, csrf_token)

        session_id = request.cookies.get("session_id")
        if not session_id or session_id != sid_from_csrf:
            raise AuthenticationException("Invalid or expired session")

        new_access_token = await token(db, redis_client, session_id)
        response_data = TokenResponse(
            access_token=new_access_token,
            expires_at=datetime.now().astimezone() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return APIResponse(code=200, message="Token refreshed successfully", data=response_data)
    except AuthenticationException as e:
        raise HTTPException(status_code=401, detail=e.message)
    except NotFoundException:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/csrf-token",
    response_model=APIResponse[CsrfTokenResponse],
    response_model_exclude_none=True,
    summary="Get CSRF token",
    responses=parse_responses({
        200: ("CSRF token retrieved successfully", CsrfTokenResponse),
        401: ("Invalid or expired session", None),
    }, common_responses),
)
async def csrf_token_api(
    request: Request,
    response: Response,
    redis_client=Depends(get_redis),
):
    """Issue CSRF token for the current session (cookie-based)."""
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise AuthenticationException("Invalid or expired session")

        csrf_token = await get_or_create_csrf_token(redis_client, session_id)
        _set_csrf_cookie(response, csrf_token)

        response_data = CsrfTokenResponse(
            csrf_token=csrf_token,
            expires_at=datetime.now().astimezone()
            + timedelta(minutes=settings.CSRF_TOKEN_EXPIRE_MINUTES),
        )
        return APIResponse(code=200, message="CSRF token retrieved successfully", data=response_data)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/reset-password",
    response_model=APIResponse[UserLoginResponse],
    response_model_exclude_none=True,
    summary="Reset password with token",
    responses=parse_responses({
        200: ("Password reset successfully", UserLoginResponse),
        401: ("Invalid or expired token", None),
        404: ("User not found", None)
    }, common_responses)
)
async def reset_password_api(
    request: Request,
    response: Response,
    request_data: ResetPasswordRequest,
    token: dict = Depends(verify_password_reset_token),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Reset password using token"""
    try:
        client_ip = get_real_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        result = await reset_password(db, redis_client, token, request_data.new_password, client_ip, user_agent)
        
        user = result["user"]
        session_id = result["session_id"]
        access_token = result["access_token"]
        csrf_token = result["csrf_token"]
        
        user_response = UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone
        )
        
        response_data = UserLoginResponse(
            access_token=access_token,
            expires_at=datetime.now().astimezone() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            user=user_response
        )

        _set_session_cookie(response, session_id)
        _set_csrf_cookie(response, csrf_token)
        
        return APIResponse(code=200, message="Password reset successfully", data=response_data)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception:
        raise HTTPException(status_code=500)

@router.get(
    "/validate-reset-token",
    response_model=APIResponse[TokenValidationResponse],
    response_model_exclude_none=True,
    summary="Validate password reset token",
    responses=parse_responses({
        200: ("Token is valid", TokenValidationResponse)
    }, common_responses)
)
async def validate_reset_token_api(
    token: dict = Depends(verify_password_reset_token),
    db: AsyncSession = Depends(get_db)
):
    """Validate password reset token without consuming it"""
    try:
        result = await validate_password_reset_token(db, token)
        return APIResponse(code=200, message="Token is valid", data=result)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception:
        raise HTTPException(status_code=500)


@router.post(
    "/forgot-password",
    response_model=APIResponse[None],
    response_model_exclude_none=True,
    summary="Send reset password email",
    responses=parse_responses({
        200: ("Reset password email sent", None),
        400: ("Please wait before requesting another password reset email", None),
        403: ("Account is disabled", None),
        404: ("User not registered", None),
        503: ("SMTP is disabled", None),
    }, common_responses),
)
async def forgot_password_api(
    request: Request,
    request_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    mailer: SMTPMailer = Depends(get_mailer),
    redis_client = Depends(get_redis),
):
    """
    Send password reset email based on input email.
    """
    try:
        await forgot_password(db, request_data.email, mailer, redis_client)        
        return APIResponse(code=200, message="Reset password email sent")
    except ValidationException:
        raise HTTPException(status_code=400, detail="Please wait before requesting another password reset email")
    except AuthenticationException:
        raise HTTPException(status_code=403, detail="Account is disabled")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not registered")
    except SMTPNotConfiguredException:
        raise HTTPException(status_code=503, detail="SMTP is disabled")
    except Exception:
        raise HTTPException(status_code=500)

@router.get(
    "/forgot-password/cooldown",
    response_model=APIResponse[PasswordResetCooldownResponse],
    response_model_exclude_none=True,
    summary="Get password reset email cooldown status",
    responses=parse_responses({
        200: ("Cooldown status retrieved", PasswordResetCooldownResponse),
    }, common_responses),
)
async def get_password_reset_cooldown_api(
    email: str = Query(..., description="Email address to check cooldown for"),
    redis_client = Depends(get_redis),
):
    """
    Get remaining cooldown time for password reset email.
    Returns 0 if no cooldown is active.
    """
    try:
        result = await get_password_reset_cooldown(email, redis_client)
        response_data = PasswordResetCooldownResponse(
            cooldown_seconds=result["cooldown_seconds"]
        )
        return APIResponse(code=200, message="Cooldown status retrieved", data=response_data)
    except Exception:
        raise HTTPException(status_code=500)

@router.get(
    "/verify-email",
    response_model=APIResponse[UserLoginResponse],
    response_model_exclude_none=True,
    summary="Verify email address",
    responses=parse_responses({
        200: ("Email verified successfully", UserLoginResponse),
        401: ("Invalid or expired token", None),
        404: ("User not found", None),
        409: ("Email already exists", None)
    }, common_responses)
)
async def verify_email_api(
    request: Request,
    response: Response,
    token: dict = Depends(verify_email_verification_token),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Verify email address using token and create session"""
    try:
        client_ip = get_real_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        result = await verify_email(db, redis_client, token, client_ip, user_agent)
        
        user = result["user"]
        session_id = result["session_id"]
        access_token = result["access_token"]
        csrf_token = result["csrf_token"]
        
        user_response = UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone
        )
        
        response_data = UserLoginResponse(
            access_token=access_token,
            expires_at=datetime.now().astimezone() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            user=user_response
        )

        _set_session_cookie(response, session_id)
        _set_csrf_cookie(response, csrf_token)
        
        return APIResponse(code=200, message="Email verified successfully", data=response_data)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except ConflictException:
        raise HTTPException(status_code=409, detail="Email already exists")
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/resend-verification",
    response_model=APIResponse[None],
    response_model_exclude_none=True,
    summary="Resend email verification",
    responses=parse_responses({
        200: ("Verification email sent", None),
        400: ("Please wait before requesting another verification email", None),
        403: ("Account is disabled", None),
        404: ("User not registered", None),
        503: ("SMTP is disabled", None),
    }, common_responses)
)
async def resend_verification_api(
    request: Request,
    request_data: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
    mailer: SMTPMailer = Depends(get_mailer),
    redis_client = Depends(get_redis),
):
    """Resend email verification email"""
    try:
        await resend_verification_email(db, request_data.email, mailer, redis_client)
        return APIResponse(code=200, message="Verification email sent")
    except ValidationException:
        raise HTTPException(status_code=400, detail="Please wait before requesting another verification email")
    except AuthenticationException:
        raise HTTPException(status_code=403, detail="Account is disabled")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not registered")
    except SMTPNotConfiguredException:
        raise HTTPException(status_code=503, detail="SMTP is disabled")
    except Exception:
        raise HTTPException(status_code=500)

@router.get(
    "/resend-verification/cooldown",
    response_model=APIResponse[PasswordResetCooldownResponse],
    response_model_exclude_none=True,
    summary="Get email verification cooldown status",
    responses=parse_responses({
        200: ("Cooldown status retrieved", PasswordResetCooldownResponse),
    }, common_responses),
)
async def get_email_verification_cooldown_api(
    email: str = Query(..., description="Email address to check cooldown for"),
    redis_client = Depends(get_redis),
):
    """
    Get remaining cooldown time for email verification email.
    Returns 0 if no cooldown is active.
    """
    try:
        cooldown_key = f"email_verification_cooldown:{email}"
        remaining_seconds = await redis_client.ttl(cooldown_key)
        
        # TTL returns -1 if key exists but has no expiry, -2 if key doesn't exist
        if remaining_seconds < 0:
            remaining_seconds = 0
        
        response_data = PasswordResetCooldownResponse(
            cooldown_seconds=remaining_seconds
        )
        return APIResponse(code=200, message="Cooldown status retrieved", data=response_data)
    except Exception:
        raise HTTPException(status_code=500)

def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,
    )


def _set_csrf_cookie(response: Response, csrf_token: str) -> None:
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.CSRF_TOKEN_EXPIRE_MINUTES * 60,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("session_id")
    response.delete_cookie("csrf_token")