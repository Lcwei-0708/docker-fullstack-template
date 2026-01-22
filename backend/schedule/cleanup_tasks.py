import logging
from datetime import datetime
from sqlalchemy import delete, or_, select, update, func
from core.database import AsyncSessionLocal
from models.user_sessions import UserSessions
from models.email_verification_tokens import EmailVerificationTokens
from models.users import Users

class CleanupTasks:
    def __init__(self):
        self.logger = logging.getLogger("schedule")

    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions and inactive sessions"""
        async with AsyncSessionLocal() as db:
            try:
                expired_sessions = await db.execute(
                    delete(UserSessions).where(
                        or_(
                            UserSessions.expires_at < datetime.now().astimezone(),
                            UserSessions.is_active == False
                        )
                    )
                )
                await db.commit()
                self.logger.info(f"Cleaned up {expired_sessions.rowcount} expired or inactive sessions")
            except Exception as e:
                self.logger.error(f"Failed to cleanup expired sessions: {e}")
                await db.rollback()

    async def cleanup_expired_email_verifications(self):
        """Cleanup expired email verification tokens and pending emails"""
        async with AsyncSessionLocal() as db:
            try:
                now = datetime.now().astimezone()
                expired_emails_subquery = (
                    select(EmailVerificationTokens.email)
                    .group_by(EmailVerificationTokens.email)
                    .having(func.max(EmailVerificationTokens.expires_at) < now)
                )

                await db.execute(
                    update(Users)
                    .where(Users.pending_email.in_(expired_emails_subquery))
                    .values(pending_email=None)
                )

                expired_tokens = await db.execute(
                    delete(EmailVerificationTokens)
                    .where(EmailVerificationTokens.email.in_(expired_emails_subquery))
                )

                await db.commit()
                self.logger.info(
                    f"Cleaned up {expired_tokens.rowcount} expired email verification tokens"
                )
            except Exception as e:
                self.logger.error(f"Failed to cleanup expired email verifications: {e}")
                await db.rollback()