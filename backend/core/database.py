from core.config import settings
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def make_async_url(url: str) -> str:
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+aiomysql://", 1)
    if url.startswith("mysql+pymysql://"):
        return url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)
    return url

# Async engine/session for API
async_engine = create_async_engine(
    make_async_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_size=settings.DB_POOL_SIZE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args={
        "charset": "utf8mb4",
    }
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)

# Sync engine/session for migration and schedule
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_size=settings.DB_POOL_SIZE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args={
        "charset": "utf8mb4",
        "connect_timeout": settings.DB_CONNECT_TIMEOUT,
        "read_timeout": settings.DB_READ_TIMEOUT,
        "write_timeout": settings.DB_WRITE_TIMEOUT,
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

def init_db():
    """
    Initialize the database (create tables).
    Call this function at startup if you want to auto-create tables.
    """
    pass