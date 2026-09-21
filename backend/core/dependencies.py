import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal, SessionLocal
from utils.custom_exception import BaseServiceException

logger = logging.getLogger("dependencies")


# Async DB dependency
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except HTTPException, BaseServiceException:
            # Client/auth business exceptions — rollback only, do not treat as DB faults
            await db.rollback()
            raise
        except Exception as e:
            logger.error("Database error: %s", e, exc_info=True)
            await db.rollback()
            raise e


# Sync DB dependency (for migration/schedule)
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    except BaseServiceException:
        db.rollback()
        raise
    except Exception as e:
        logger.error("Database error: %s", e, exc_info=True)
        db.rollback()
        raise e
    finally:
        db.close()
