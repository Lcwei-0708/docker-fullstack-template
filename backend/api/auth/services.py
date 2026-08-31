import ast
from datetime import datetime, timedelta
from urllib.parse import quote

import redis
from jose import JWTError, jwt
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import (
    clear_user_all_sessions,
    create_access_token,
    create_csrf_token,
    create_email_verification_token,
    create_password_reset_token,
    extend_session_ttl,
    hash_password,
    verify_password,
)
from extensions.smtp import SMTPMailer
from models.email_verification_tokens import EmailVerificationTokens
from models.login_logs import LoginLogs
from models.password_reset_tokens import PasswordResetTokens
from models.user_sessions import UserSessions
from models.users import Users
from utils.custom_exception import (
    AuthenticationException,
    ConflictException,
    EmailVerificationRequiredException,
    NotFoundException,
    PasswordResetRequiredException,
    RegistrationDisabledException,
    ServerException,
    SMTPNotConfiguredException,
    ValidationException,
)
from utils.email_templates import (
    EMAIL_VERIFICATION_TEMPLATE,
    PASSWORD_RESET_TEMPLATE,
)

from .schema import (
    ActionRequiredResponse,
    LoginResult,
    SessionResult,
    TokenValidationResponse,
    UserLogin,
    UserRegister,
)


async def register(
    db: AsyncSession,
    redis_client: redis.Redis,
    user_data: UserRegister,
    ip_address: str,
    user_agent: str,
    mailer: SMTPMailer | None = None,
) -> LoginResult:
    """User register"""
    if not settings.REGISTRATION_ENABLE:
        raise RegistrationDisabledException("Registration is disabled")

    user = await _create_user(db, user_data)

    # Check if email verification is required
    if settings.EMAIL_VERIFICATION_ENABLE and settings.SMTP_ENABLE and mailer:
        # Check cooldown
        cooldown_key = f"email_verification_cooldown:{user.email}"
        remaining_seconds = await redis_client.ttl(cooldown_key)

        if remaining_seconds > 0:
            # In cooldown, return 202 without data
            await _log_login_attempt(
                db,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                is_success=True,
                user_id=user.id,
            )
            raise EmailVerificationRequiredException(
                message="Email verification required", details=None
            )
        else:
            # Not in cooldown, send verification email
            await _send_registration_verification_email(db, mailer, user)

            # Set cooldown
            await redis_client.setex(
                cooldown_key, settings.EMAIL_VERIFICATION_COOLDOWN_SECONDS, "1"
            )

            await _log_login_attempt(
                db,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                is_success=True,
                user_id=user.id,
            )
            raise EmailVerificationRequiredException(
                message="Email verification required", details=None
            )

    session_result = await _create_user_session(db, redis_client, user, ip_address, user_agent)
    await _log_login_attempt(
        db,
        email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        is_success=True,
        user_id=user.id,
    )
    return {
        "user": user,
        "session_id": session_result["session_id"],
        "access_token": session_result["access_token"],
        "csrf_token": session_result["csrf_token"],
    }


async def login(
    db: AsyncSession,
    redis_client: redis.Redis,
    login_data: UserLogin,
    ip_address: str,
    user_agent: str,
    mailer: SMTPMailer | None = None,
) -> LoginResult:
    """User login"""
    result = await db.execute(select(Users).where(Users.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user:
        await _log_login_attempt(
            db,
            email=login_data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            is_success=False,
            failure_reason="User not found",
        )
        raise AuthenticationException("Invalid email or password")

    # Check if user account is disabled
    if not user.status:
        await _log_login_attempt(
            db,
            email=login_data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            is_success=False,
            failure_reason="Account disabled",
        )
        raise AuthenticationException("Account is disabled")

    # Now verify password
    if not await verify_password(login_data.password, user.hash_password):
        await _log_login_attempt(
            db,
            email=login_data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            is_success=False,
            failure_reason="Invalid password",
        )
        raise AuthenticationException("Invalid email or password")

    # Check if password reset is required
    if user.password_reset_required:
        reset_token = await create_password_reset_token(user.id, user.email)

        reset_token_record = PasswordResetTokens(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.now().astimezone()
            + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
        db.add(reset_token_record)
        await db.commit()

        await _log_login_attempt(
            db,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            is_success=True,
            user_id=user.id,
        )

        raise PasswordResetRequiredException(
            message="Password reset required",
            details=ActionRequiredResponse(
                action_type="password_reset",
                token=reset_token,
                expires_at=reset_token_record.expires_at.isoformat()
                if reset_token_record.expires_at
                else None,
            ),
        )

    # Check if email verification is required
    if settings.EMAIL_VERIFICATION_ENABLE and settings.SMTP_ENABLE and mailer:
        if not user.email_verified:
            # Check cooldown
            cooldown_key = f"email_verification_cooldown:{user.email}"
            remaining_seconds = await redis_client.ttl(cooldown_key)

            if remaining_seconds > 0:
                # In cooldown, return 202 with cooldown time
                await _log_login_attempt(
                    db,
                    email=user.email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    is_success=True,
                    user_id=user.id,
                )
                # Calculate expires_at from cooldown
                expires_at = (
                    datetime.now().astimezone() + timedelta(seconds=remaining_seconds)
                ).isoformat()
                raise EmailVerificationRequiredException(
                    message="Email verification required",
                    details=ActionRequiredResponse(
                        action_type="email_verification", token=None, expires_at=expires_at
                    ),
                )
            else:
                # Not in cooldown, send verification email
                await _send_registration_verification_email(db, mailer, user)

                # Set cooldown
                await redis_client.setex(
                    cooldown_key, settings.EMAIL_VERIFICATION_COOLDOWN_SECONDS, "1"
                )

                await _log_login_attempt(
                    db,
                    email=user.email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    is_success=True,
                    user_id=user.id,
                )
                # Calculate expires_at from cooldown
                expires_at = (
                    datetime.now().astimezone()
                    + timedelta(seconds=settings.EMAIL_VERIFICATION_COOLDOWN_SECONDS)
                ).isoformat()
                raise EmailVerificationRequiredException(
                    message="Email verification required",
                    details=ActionRequiredResponse(
                        action_type="email_verification", token=None, expires_at=expires_at
                    ),
                )

    session_result = await _create_user_session(db, redis_client, user, ip_address, user_agent)
    await _log_login_attempt(
        db,
        email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        is_success=True,
        user_id=user.id,
    )
    return {
        "user": user,
        "session_id": session_result["session_id"],
        "access_token": session_result["access_token"],
        "csrf_token": session_result["csrf_token"],
    }


async def logout(
    db: AsyncSession, redis_client: redis.Redis, user_id: str, session_id: str
) -> bool:
    """User logout"""
    try:
        redis_key = f"session:{session_id}"
        await redis_client.delete(redis_key, f"csrf:{session_id}")

        result = await db.execute(
            select(UserSessions).where(
                UserSessions.user_id == user_id, UserSessions.id == session_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await db.commit()

        return True
    except Exception:
        raise ServerException("Logout failed")


async def logout_all_devices(db: AsyncSession, redis_client: redis.Redis, user_id: str) -> bool:
    """Logout user from all devices"""
    try:
        return await clear_user_all_sessions(db, redis_client, user_id)
    except Exception:
        raise ServerException("Failed to logout all devices")


async def get_or_create_csrf_token(
    redis_client: redis.Redis,
    session_id: str,
) -> str:
    """Return existing CSRF token or create a new one (does not extend TTL)."""
    session_raw = await redis_client.get(f"session:{session_id}")
    if not session_raw:
        raise AuthenticationException("Invalid or expired session")

    existing = await redis_client.get(_csrf_redis_key(session_id))
    if existing:
        return existing.decode() if isinstance(existing, bytes) else existing

    return await _create_csrf_token_for_session(redis_client, session_id)


async def verify_csrf_token(
    redis_client: redis.Redis,
    csrf_token: str | None,
) -> str:
    """Validate CSRF token and return session_id."""
    if not csrf_token:
        raise AuthenticationException("Invalid or expired CSRF token")

    try:
        payload = jwt.decode(
            csrf_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise AuthenticationException("Invalid or expired CSRF token")

    if payload.get("token_type") != "csrf":
        raise AuthenticationException("Invalid or expired CSRF token")

    session_id = payload.get("sid")
    if not session_id:
        raise AuthenticationException("Invalid or expired CSRF token")

    stored = await redis_client.get(_csrf_redis_key(session_id))
    if not stored:
        raise AuthenticationException("Invalid or expired CSRF token")

    stored_token = stored.decode() if isinstance(stored, bytes) else stored
    if stored_token != csrf_token:
        raise AuthenticationException("Invalid or expired CSRF token")

    return session_id


async def token(db: AsyncSession, redis_client: redis.Redis, session_id: str) -> str:
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

    # Verify user exists
    user = await _get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")

    if not user.status:
        raise AuthenticationException("Account is disabled")

    new_access_token = await create_access_token(
        data={"sub": user_id, "email": user.email, "sid": session_id}
    )

    data["access_token"] = new_access_token
    await extend_session_ttl(redis_client, session_id, data)
    await _update_session_expiry(db, session_id)

    return new_access_token


async def reset_password(
    db: AsyncSession,
    redis_client: redis.Redis,
    token: dict,
    new_password: str,
    ip_address: str,
    user_agent: str,
) -> LoginResult:
    """Reset password using token"""
    try:
        user_id = token.get("sub")
        token_string = token.get("token")

        result = await db.execute(
            select(PasswordResetTokens).where(
                PasswordResetTokens.token == token_string,
                PasswordResetTokens.user_id == user_id,
                not PasswordResetTokens.is_used,
                PasswordResetTokens.expires_at > datetime.now().astimezone(),
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise AuthenticationException("Invalid or expired token")

        result = await db.execute(select(Users).where(Users.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        user.hash_password = await hash_password(new_password)
        user.password_reset_required = False

        token_record.is_used = True

        # Force logout all devices
        await clear_user_all_sessions(db, redis_client, user_id)

        # Create new session
        session_result = await _create_user_session(db, redis_client, user, ip_address, user_agent)

        await db.commit()

        return {
            "user": user,
            "session_id": session_result["session_id"],
            "access_token": session_result["access_token"],
            "csrf_token": session_result["csrf_token"],
        }

    except AuthenticationException, NotFoundException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to reset password: {str(e)}")


async def validate_password_reset_token(db: AsyncSession, token: dict) -> TokenValidationResponse:
    """Validate password reset token without consuming it"""
    try:
        user_id = token.get("sub")
        token_string = token.get("token")

        result = await db.execute(
            select(PasswordResetTokens).where(
                PasswordResetTokens.token == token_string,
                PasswordResetTokens.user_id == user_id,
                not PasswordResetTokens.is_used,
                PasswordResetTokens.expires_at > datetime.now().astimezone(),
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise AuthenticationException("Invalid or expired token")

        result = await db.execute(select(Users).where(Users.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.status:
            raise AuthenticationException("User not found or account disabled")

        return TokenValidationResponse(is_valid=True)

    except AuthenticationException:
        raise
    except Exception as e:
        raise ServerException(f"Token validation failed: {str(e)}")


async def forgot_password(
    db: AsyncSession,
    email: str,
    mailer: SMTPMailer,
    redis_client: redis.Redis,
) -> dict:
    """
    Forgot password and send reset password email
    """
    try:
        user = await _get_user_by_email_for_password_reset(db, email)

        if not getattr(mailer, "enabled", False):
            raise SMTPNotConfiguredException("SMTP is disabled")

        cooldown_key = f"password_reset_cooldown:{email}"
        remaining_seconds = await redis_client.ttl(cooldown_key)

        if remaining_seconds > 0:
            raise ValidationException(
                (
                    f"Please wait {remaining_seconds} seconds before requesting "
                    "another password reset email"
                ),
                details={"cooldown_seconds": remaining_seconds},
            )

        token_meta = await _request_password_reset_email(db, user)
        reset_token = token_meta["reset_token"]
        reset_url = (
            f"http{'s' if settings.SSL_ENABLE else ''}://"
            f"{settings.HOSTNAME}:{settings.FRONTEND_PORT}"
            f"/auth/reset-password?token={quote(reset_token, safe='')}"
        )

        # Render email template with user name and app name
        user_name = f"{user.first_name} {user.last_name}".strip()
        app_name = settings.PROJECT_NAME

        email_content = PASSWORD_RESET_TEMPLATE.render(
            reset_url=reset_url,
            user_name=user_name,
            app_name=app_name,
        )

        mailer.send_text(
            to_emails=[email],
            subject=email_content["subject"],
            body=email_content["body"],
            html_body=email_content.get("html_body"),
        )

        # Set cooldown period in Redis
        await redis_client.setex(cooldown_key, settings.PASSWORD_RESET_EMAIL_COOLDOWN_SECONDS, "1")

        return {**token_meta, "reset_url": reset_url}

    except (
        NotFoundException,
        AuthenticationException,
        SMTPNotConfiguredException,
        ValidationException,
    ):
        raise
    except Exception as e:
        raise ServerException(f"Failed to send password reset email: {str(e)}")


async def get_password_reset_cooldown(
    email: str,
    redis_client: redis.Redis,
) -> dict:
    """
    Get remaining cooldown time for password reset email.

    Returns:
        Dict with 'cooldown_seconds' (0 if no cooldown active)
    """
    cooldown_key = f"password_reset_cooldown:{email}"
    remaining_seconds = await redis_client.ttl(cooldown_key)

    # TTL returns -1 if key exists but has no expiry, -2 if key doesn't exist
    if remaining_seconds < 0:
        remaining_seconds = 0

    return {"cooldown_seconds": remaining_seconds}


async def _update_session_expiry(db: AsyncSession, session_id: str) -> None:
    """Update session expiry time in database"""
    try:
        result = await db.execute(select(UserSessions).where(UserSessions.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            session.expires_at = datetime.now().astimezone() + timedelta(
                minutes=settings.SESSION_EXPIRE_MINUTES
            )
            await db.commit()
    except Exception as e:
        raise ServerException(f"Failed to update session expiry in database: {e}")


async def _create_user(db: AsyncSession, user_data: UserRegister) -> Users:
    try:
        result = await db.execute(
            select(Users).where(
                or_(Users.email == user_data.email, Users.pending_email == user_data.email)
            )
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ConflictException("Email already exists")

        user = Users(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            hash_password=await hash_password(user_data.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except ConflictException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to create user: {str(e)}")


async def _get_user_by_id(db: AsyncSession, user_id: str) -> Users | None:
    result = await db.execute(select(Users).where(Users.id == user_id))
    return result.scalar_one_or_none()


async def _create_user_session(
    db: AsyncSession, redis_client: redis.Redis, user: Users, ip_address: str, user_agent: str
) -> SessionResult:
    try:
        session = UserSessions(
            user_id=user.id,
            jwt_access_token="",
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now().astimezone()
            + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        session_id = session.id
        access_token = await create_access_token(
            data={"sub": user.id, "email": user.email, "sid": session_id}
        )

        session.jwt_access_token = access_token
        await db.commit()

        redis_key = f"session:{session_id}"
        session_data = {
            "user_id": user.id,
            "email": user.email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "access_token": access_token,
            "created_at": datetime.now().astimezone().isoformat(),
            "last_activity": datetime.now().astimezone().isoformat(),
        }

        await redis_client.setex(redis_key, settings.SESSION_EXPIRE_MINUTES * 60, str(session_data))

        csrf_token = await _create_csrf_token_for_session(redis_client, session_id)

        return {
            "session_id": session_id,
            "access_token": access_token,
            "csrf_token": csrf_token,
        }
    except Exception as e:
        raise ServerException(f"Failed to create user session: {str(e)}")


async def _log_login_attempt(
    db: AsyncSession,
    email: str,
    ip_address: str,
    user_agent: str,
    is_success: bool,
    user_id: str | None = None,
    failure_reason: str | None = None,
) -> None:
    log = LoginLogs(
        user_id=user_id,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        is_success=is_success,
        failure_reason=failure_reason,
    )
    db.add(log)
    await db.commit()


async def _get_user_by_email_for_password_reset(db: AsyncSession, email: str) -> Users:
    result = await db.execute(select(Users).where(Users.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not registered")
    if not user.status:
        raise AuthenticationException("Account is disabled")
    return user


async def _request_password_reset_email(
    db: AsyncSession,
    user: Users,
) -> dict:
    """
    Create a password reset token record for the user and return token metadata.
    Invalidates all previous unused tokens for this user before creating a new one.
    """
    now = datetime.now().astimezone()
    expires_at = now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

    # Invalidate all previous unused tokens for this user
    await db.execute(
        update(PasswordResetTokens)
        .where(PasswordResetTokens.user_id == user.id, not PasswordResetTokens.is_used)
        .values(is_used=True)
    )

    reset_token = await create_password_reset_token(user.id, user.email)
    reset_token_record = PasswordResetTokens(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at,
    )
    db.add(reset_token_record)
    await db.commit()

    return {
        "reset_token": reset_token,
        "expires_at": expires_at,
        "user_id": user.id,
    }


async def verify_email(
    db: AsyncSession, redis_client: redis.Redis, token: dict, ip_address: str, user_agent: str
) -> LoginResult:
    """Verify email using token and create session"""
    try:
        user_id = token.get("sub")
        email = token.get("email")
        verification_type = token.get("verification_type")
        token_string = token.get("token")

        # Verify token record exists and is valid
        result = await db.execute(
            select(EmailVerificationTokens).where(
                EmailVerificationTokens.token == token_string,
                EmailVerificationTokens.user_id == user_id,
                EmailVerificationTokens.email == email,
                EmailVerificationTokens.token_type == verification_type,
                not EmailVerificationTokens.is_used,
                EmailVerificationTokens.expires_at > datetime.now().astimezone(),
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise AuthenticationException("Invalid or expired token")

        # Get user
        result = await db.execute(select(Users).where(Users.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if not user.status:
            raise AuthenticationException("Account is disabled")

        # Mark token as used
        token_record.is_used = True

        if verification_type == "registration":
            # Mark email as verified
            user.email_verified = True
        elif verification_type == "email_change":
            # Update email from pending_email to email
            if user.pending_email != email:
                raise AuthenticationException("Email mismatch")

            # Check if new email already exists
            result = await db.execute(
                select(Users).where(Users.email == email, Users.id != user_id)
            )
            if result.scalar_one_or_none():
                raise ConflictException("Email already exists")

            user.email = email
            user.pending_email = None
            user.email_verified = True

        # Create session for verified user
        session_result = await _create_user_session(db, redis_client, user, ip_address, user_agent)

        await db.commit()

        return {
            "user": user,
            "session_id": session_result["session_id"],
            "access_token": session_result["access_token"],
            "csrf_token": session_result["csrf_token"],
        }

    except AuthenticationException, NotFoundException, ConflictException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to verify email: {str(e)}")


async def resend_verification_email(
    db: AsyncSession,
    email: str,
    mailer: SMTPMailer,
    redis_client: redis.Redis,
) -> dict:
    """Resend email verification"""
    try:
        user = await _get_user_by_email_for_password_reset(db, email)

        if not settings.SMTP_ENABLE or not getattr(mailer, "enabled", False):
            raise SMTPNotConfiguredException("SMTP is disabled")

        # Check cooldown
        cooldown_key = f"email_verification_cooldown:{email}"
        remaining_seconds = await redis_client.ttl(cooldown_key)

        if remaining_seconds > 0:
            raise ValidationException(
                (
                    f"Please wait {remaining_seconds} seconds before requesting "
                    "another verification email"
                ),
                details={"cooldown_seconds": remaining_seconds},
            )

        # Determine verification type
        if user.email_verified:
            # If email is already verified but there's a pending email, resend email change
            # verification
            if user.pending_email:
                token_meta = await _request_email_change_verification_email(
                    db, user, user.pending_email
                )
                verification_url = (
                    f"http{'s' if settings.SSL_ENABLE else ''}://"
                    f"{settings.HOSTNAME}:{settings.FRONTEND_PORT}"
                    f"/auth/verify-email?token={quote(token_meta['verification_token'], safe='')}"
                )

                user_name = f"{user.first_name} {user.last_name}".strip()
                app_name = settings.PROJECT_NAME

                email_content = EMAIL_VERIFICATION_TEMPLATE.render(
                    verification_url=verification_url,
                    user_name=user_name,
                    app_name=app_name,
                    expire_minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
                )

                mailer.send_text(
                    to_emails=[user.pending_email],
                    subject=email_content["subject"],
                    body=email_content["body"],
                    html_body=email_content.get("html_body"),
                )
            else:
                raise ValidationException("Email is already verified")
        else:
            # Resend registration verification
            token_meta = await _request_registration_verification_email(db, user)
            verification_url = (
                f"http{'s' if settings.SSL_ENABLE else ''}://"
                f"{settings.HOSTNAME}:{settings.FRONTEND_PORT}"
                f"/auth/verify-email?token={quote(token_meta['verification_token'], safe='')}"
            )

            user_name = f"{user.first_name} {user.last_name}".strip()
            app_name = settings.PROJECT_NAME

            email_content = EMAIL_VERIFICATION_TEMPLATE.render(
                verification_url=verification_url,
                user_name=user_name,
                app_name=app_name,
                expire_minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
            )

            mailer.send_text(
                to_emails=[email],
                subject=email_content["subject"],
                body=email_content["body"],
                html_body=email_content.get("html_body"),
            )

        # Set cooldown
        await redis_client.setex(cooldown_key, settings.EMAIL_VERIFICATION_COOLDOWN_SECONDS, "1")

        return {"message": "Verification email sent"}

    except (
        NotFoundException,
        AuthenticationException,
        SMTPNotConfiguredException,
        ValidationException,
    ):
        raise
    except Exception as e:
        raise ServerException(f"Failed to send verification email: {str(e)}")


def _csrf_redis_key(session_id: str) -> str:
    return f"csrf:{session_id}"


async def _create_csrf_token_for_session(
    redis_client: redis.Redis,
    session_id: str,
) -> str:
    csrf_token = await create_csrf_token(session_id)
    ttl = settings.CSRF_TOKEN_EXPIRE_MINUTES * 60
    await redis_client.setex(_csrf_redis_key(session_id), ttl, csrf_token)
    return csrf_token


async def _send_registration_verification_email(
    db: AsyncSession, mailer: SMTPMailer, user: Users
) -> None:
    """Send registration verification email"""
    if not settings.SMTP_ENABLE or not getattr(mailer, "enabled", False):
        return

    token_meta = await _request_registration_verification_email(db, user)
    verification_url = (
        f"http{'s' if settings.SSL_ENABLE else ''}://"
        f"{settings.HOSTNAME}:{settings.FRONTEND_PORT}"
        f"/auth/verify-email?token={quote(token_meta['verification_token'], safe='')}"
    )

    user_name = f"{user.first_name} {user.last_name}".strip()
    app_name = settings.PROJECT_NAME

    email_content = EMAIL_VERIFICATION_TEMPLATE.render(
        verification_url=verification_url,
        user_name=user_name,
        app_name=app_name,
        expire_minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
    )

    mailer.send_text(
        to_emails=[user.email],
        subject=email_content["subject"],
        body=email_content["body"],
        html_body=email_content.get("html_body"),
    )


async def _request_registration_verification_email(
    db: AsyncSession,
    user: Users,
) -> dict:
    """Create a registration verification token record"""
    now = datetime.now().astimezone()
    expires_at = now + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)

    # Invalidate all previous unused registration tokens for this user
    await db.execute(
        update(EmailVerificationTokens)
        .where(
            EmailVerificationTokens.user_id == user.id,
            EmailVerificationTokens.token_type == "registration",
            not EmailVerificationTokens.is_used,
        )
        .values(is_used=True)
    )

    verification_token = await create_email_verification_token(user.id, user.email, "registration")
    token_record = EmailVerificationTokens(
        user_id=user.id,
        email=user.email,
        token=verification_token,
        token_type="registration",
        expires_at=expires_at,
    )
    db.add(token_record)
    await db.commit()

    return {
        "verification_token": verification_token,
        "expires_at": expires_at,
        "user_id": user.id,
    }


async def _request_email_change_verification_email(
    db: AsyncSession,
    user: Users,
    new_email: str,
) -> dict:
    """Create an email change verification token record"""
    now = datetime.now().astimezone()
    expires_at = now + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)

    # Invalidate all previous unused email_change tokens for this user
    await db.execute(
        update(EmailVerificationTokens)
        .where(
            EmailVerificationTokens.user_id == user.id,
            EmailVerificationTokens.token_type == "email_change",
            not EmailVerificationTokens.is_used,
        )
        .values(is_used=True)
    )

    verification_token = await create_email_verification_token(user.id, new_email, "email_change")
    token_record = EmailVerificationTokens(
        user_id=user.id,
        email=new_email,
        token=verification_token,
        token_type="email_change",
        expires_at=expires_at,
    )
    db.add(token_record)
    await db.commit()

    return {
        "verification_token": verification_token,
        "expires_at": expires_at,
        "user_id": user.id,
    }
