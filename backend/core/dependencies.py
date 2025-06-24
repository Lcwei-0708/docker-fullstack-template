import logging
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal, SessionLocal

logger = logging.getLogger(__name__)

# Async DB dependency
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception as e:
            logger.error(f"Database error: {e}")
            await db.rollback()
            raise e

# Sync DB dependency (for migration/schedule)
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise e
    finally:
        db.close()