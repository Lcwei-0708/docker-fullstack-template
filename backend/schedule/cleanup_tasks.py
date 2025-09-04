import logging
from datetime import datetime
from sqlalchemy import delete, or_
from core.database import AsyncSessionLocal
from models.user_sessions import UserSessions

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