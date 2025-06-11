from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# Create SQLAlchemy engine using the database URL from settings
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

def init_db():
    """
    Initialize the database (create tables).
    Call this function at startup if you want to auto-create tables.
    """
    pass