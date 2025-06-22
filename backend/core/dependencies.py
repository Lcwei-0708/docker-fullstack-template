import logging
from sqlalchemy.orm import Session
from core.database import SessionLocal

logger = logging.getLogger(__name__)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise e
    finally:
        db.close()