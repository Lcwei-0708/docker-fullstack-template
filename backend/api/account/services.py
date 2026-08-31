import logging
from urllib.parse import quote

import redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.services import _request_email_change_verification_email
from core.config import settings
from core.security import clear_user_all_sessions, hash_password, verify_password
from extensions.smtp import SMTPMailer
from models.users import Users
from utils.custom_exception import (
    AuthenticationException,
    ServerException,
    SMTPNotConfiguredException,
)
from utils.email_templates import EMAIL_VERIFICATION_TEMPLATE

from .schema import PasswordChange, UserUpdate

logger = logging.getLogger("account")


async def get_user_by_id(db: AsyncSession, user_id: str) -> Users | None:
    """Get user info by id"""
    result = await db.execute(select(Users).where(Users.id == user_id))
    return result.scalar_one_or_none()


async def update_user_profile(
    db: AsyncSession,
    user_id: str,
    user_update: UserUpdate,
    mailer: SMTPMailer | None = None,
    redis_client: redis.Redis | None = None,
) -> tuple[Users, bool] | None:
    """Update user info (excluding password)"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    email_change_requested = False
    new_email = user_update.email
    if new_email and new_email != user.email:
        result = await db.execute(
            select(Users).where(
                or_(Users.email == new_email, Users.pending_email == new_email), Users.id != user_id
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already exists")

        # Defer email change until verification completes.
        user.pending_email = new_email
        email_change_requested = True

    update_data = user_update.model_dump(exclude_unset=True)
    update_data.pop("email", None)
    for field, value in update_data.items():
        setattr(user, field, value)

    if (
        email_change_requested
        and settings.SMTP_ENABLE
        and mailer
        and getattr(mailer, "enabled", False)
    ):
        should_send = True
        if redis_client:
            cooldown_key = f"email_verification_cooldown:{new_email}"
            remaining_seconds = await redis_client.ttl(cooldown_key)
            try:
                remaining_seconds = int(remaining_seconds)
            except TypeError, ValueError:
                remaining_seconds = 0
            if remaining_seconds > 0:
                should_send = False

        if should_send:
            try:
                token_meta = await _request_email_change_verification_email(db, user, new_email)
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
                    to_emails=[new_email],
                    subject=email_content["subject"],
                    body=email_content["body"],
                    html_body=email_content.get("html_body"),
                )

                if redis_client:
                    await redis_client.setex(
                        cooldown_key, settings.EMAIL_VERIFICATION_COOLDOWN_SECONDS, "1"
                    )
            except SMTPNotConfiguredException as exc:
                logger.warning("Skip email change verification send: %s", exc)

    await db.commit()
    await db.refresh(user)
    return user, email_change_requested


async def change_password(
    db: AsyncSession,
    user_id: str,
    password_change: PasswordChange,
    redis_client=None,
    current_session_id: str | None = None,
) -> bool:
    """Change user password"""
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            return False

        if not await verify_password(password_change.current_password, user.hash_password):
            raise AuthenticationException("Current password is incorrect")

        user.hash_password = await hash_password(password_change.new_password)
        user.password_reset_required = False

        if password_change.logout_other_devices and redis_client:
            await clear_user_all_sessions(
                db,
                redis_client,
                user_id,
                exclude_session_id=current_session_id,
            )

        await db.commit()

        return True
    except AuthenticationException:
        raise
    except Exception:
        raise ServerException("Failed to change password")
