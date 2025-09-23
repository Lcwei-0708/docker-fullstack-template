import logging
from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

logger = logging.getLogger("database")

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

async def init_db():
    """
    Initialize the database (create tables and default data).
    Call this function at startup if you want to auto-create tables and default admin user.
    """
    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create default admin user if it doesn't exist
    await create_default_admin()

async def create_default_admin():
    """Create default admin user if it doesn't exist"""
    from sqlalchemy import select
    from models.users import Users
    from models.roles import Roles
    from models.role_mapper import RoleMapper
    from core.security import hash_password
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if super admin role exists, create if not
            super_role_result = await db.execute(
                select(Roles).where(Roles.name == settings.DEFAULT_SUPER_ADMIN_ROLE)
            )
            super_role = super_role_result.scalar_one_or_none()
            
            if not super_role:
                super_role = Roles(
                    name=settings.DEFAULT_SUPER_ADMIN_ROLE,
                    description="Super Administrator role with full system access"
                )
                db.add(super_role)
                await db.commit()
                await db.refresh(super_role)
                logger.info(f"Created {settings.DEFAULT_SUPER_ADMIN_ROLE} role")
            
            # Check if any user has super admin role
            super_users_result = await db.execute(
                select(Users)
                .join(RoleMapper, Users.id == RoleMapper.user_id)
                .join(Roles, RoleMapper.role_id == Roles.id)
                .where(Roles.name == settings.DEFAULT_SUPER_ADMIN_ROLE)
            )
            existing_super_users = super_users_result.scalars().all()
            
            if existing_super_users:
                logger.info(f"Super admin users already exist: {[user.email for user in existing_super_users]}")
                return
            
            # If no super admin users exist, check if default admin user exists (by email)
            result = await db.execute(
                select(Users).where(Users.email == settings.DEFAULT_ADMIN_EMAIL)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # User exists but doesn't have super role, assign super admin role
                role_mapping = RoleMapper(
                    user_id=existing_user.id,
                    role_id=super_role.id
                )
                db.add(role_mapping)
                await db.commit()
                logger.info(f"Assigned super admin role to existing user: {existing_user.email}")
                return
            
            # Create new super admin user
            admin_user = Users(
                first_name=settings.DEFAULT_ADMIN_FIRST_NAME,
                last_name=settings.DEFAULT_ADMIN_LAST_NAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                phone=settings.DEFAULT_ADMIN_PHONE,
                hash_password=await hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                status=True,
                password_reset_required=False
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            # Assign super admin role to user
            role_mapping = RoleMapper(
                user_id=admin_user.id,
                role_id=super_role.id
            )
            db.add(role_mapping)
            await db.commit()
            
            logger.info(f"Created new default super admin user: {settings.DEFAULT_ADMIN_EMAIL}")
            
        except Exception as e:
            logger.error(f"Error creating default admin user: {str(e)}")
            await db.rollback()