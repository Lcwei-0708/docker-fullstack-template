import logging

from sqlalchemy import delete, select, text

from core.config import settings
from core.database import AsyncSessionLocal
from core.permissions import get_attributes
from core.security import hash_password
from models.role_attributes import RoleAttributes
from models.role_mapper import RoleMapper
from models.roles import Roles
from models.users import Users

logger = logging.getLogger("init_db")


async def is_already_initialized() -> bool:
    """Return True if super admin role and user already exist (seed done)."""
    async with AsyncSessionLocal() as db:
        # Super admin role must exist
        super_role_result = await db.execute(
            select(Roles).where(Roles.name == settings.DEFAULT_SUPER_ADMIN_ROLE)
        )
        super_role = super_role_result.scalar_one_or_none()
        if not super_role:
            return False

        # At least one attribute must exist
        attrs_result = await db.execute(select(RoleAttributes))
        if not attrs_result.scalars().first():
            return False

        # If any user already mapped to super admin role, consider seeded
        super_users_result = await db.execute(
            select(Users)
            .join(RoleMapper, Users.id == RoleMapper.user_id)
            .where(RoleMapper.role_id == super_role.id)
        )
        if super_users_result.scalars().first():
            return True

        return False


async def init_database():
    """Initialize database with default data: role attributes, roles and admin account"""
    lock_name = "init_db_lock"
    lock_timeout_sec = 15

    # Use DB advisory lock to avoid multiple workers seeding simultaneously
    async with AsyncSessionLocal() as lock_session:
        lock_result = await lock_session.execute(
            text("SELECT GET_LOCK(:name, :timeout)"),
            {"name": lock_name, "timeout": lock_timeout_sec},
        )
        lock_acquired = lock_result.scalar()

        if lock_acquired != 1:
            logger.info("Skipping database initialization: another worker is seeding.")
            return

        try:
            # Double-check after getting the lock, if already initialized, skip
            if await is_already_initialized():
                logger.info("Database initialization already completed, skipping.")
                return

            logger.info("Starting database initialization...")

            await create_role_attributes()
            await create_default_roles()
            await create_default_admin()

            logger.info("Database initialization completed")

        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
        finally:
            # Always release the advisory lock
            await lock_session.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})
            await lock_session.commit()


async def create_role_attributes():
    """Create role attributes"""
    async with AsyncSessionLocal() as db:
        try:
            attributes = get_attributes()
            created_count = 0
            updated_count = 0

            for attr_config in attributes:
                existing_attr = await db.execute(
                    select(RoleAttributes).where(RoleAttributes.name == attr_config["name"])
                )
                existing = existing_attr.scalar_one_or_none()
                if existing:
                    if (
                        getattr(existing, "group", None) is None
                        and attr_config.get("group") is not None
                    ):
                        existing.group = attr_config.get("group")
                        updated_count += 1
                    if (
                        getattr(existing, "category", None) is None
                        and attr_config.get("category") is not None
                    ):
                        existing.category = attr_config.get("category")
                        updated_count += 1
                    continue

                attribute = RoleAttributes(
                    name=attr_config["name"],
                    group=attr_config.get("group"),
                    category=attr_config.get("category"),
                )
                db.add(attribute)
                created_count += 1

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to create role attributes: {str(e)}")
            await db.rollback()
            raise


async def create_default_roles():
    """Create system super-admin role and a basic user role."""
    async with AsyncSessionLocal() as db:
        try:
            default_roles = [
                {
                    "name": settings.DEFAULT_SUPER_ADMIN_ROLE,
                    "description": "System super administrator (full access bypass)",
                    "level": settings.DEFAULT_SUPER_ADMIN_LEVEL,
                },
                {
                    "name": "user",
                    "description": "Regular user role with basic permissions",
                    "level": settings.DEFAULT_USER_ROLE_LEVEL,
                },
            ]

            created_count = 0

            for role_config in default_roles:
                existing_role = await db.execute(
                    select(Roles).where(Roles.name == role_config["name"])
                )
                if existing_role.scalar_one_or_none():
                    continue

                role = Roles(
                    name=role_config["name"],
                    description=role_config["description"],
                    level=role_config["level"],
                )
                db.add(role)
                created_count += 1

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to create roles: {str(e)}")
            await db.rollback()
            raise


async def create_default_admin():
    """Create default super-admin account from ENV settings."""
    async with AsyncSessionLocal() as db:
        try:
            super_role_result = await db.execute(
                select(Roles).where(Roles.name == settings.DEFAULT_SUPER_ADMIN_ROLE)
            )
            super_role = super_role_result.scalar_one_or_none()

            if not super_role:
                logger.error("Super admin role not found, please run role initialization first")
                return

            super_users_result = await db.execute(
                select(Users)
                .join(RoleMapper, Users.id == RoleMapper.user_id)
                .join(Roles, RoleMapper.role_id == Roles.id)
                .where(Roles.name == settings.DEFAULT_SUPER_ADMIN_ROLE)
            )
            existing_super_users = super_users_result.scalars().all()

            if existing_super_users:
                logger.info(
                    "Super admin users already exist: "
                    f"{[user.email for user in existing_super_users]}"
                )
                await db.commit()
                return

            existing_user_result = await db.execute(
                select(Users).where(Users.email == settings.DEFAULT_ADMIN_EMAIL)
            )
            existing_user = existing_user_result.scalar_one_or_none()

            if existing_user:
                existing_role_mapping = await db.execute(
                    select(RoleMapper).where(
                        RoleMapper.user_id == existing_user.id, RoleMapper.role_id == super_role.id
                    )
                )
                if not existing_role_mapping.scalar_one_or_none():
                    role_mapping = RoleMapper(user_id=existing_user.id, role_id=super_role.id)
                    db.add(role_mapping)
                    logger.info(
                        f"Assigned super admin role to existing user: {existing_user.email}"
                    )
                await db.execute(
                    delete(RoleMapper).where(
                        RoleMapper.user_id == existing_user.id,
                        RoleMapper.role_id != super_role.id,
                    )
                )
            else:
                admin_user = Users(
                    first_name=settings.DEFAULT_ADMIN_FIRST_NAME,
                    last_name=settings.DEFAULT_ADMIN_LAST_NAME,
                    email=settings.DEFAULT_ADMIN_EMAIL,
                    phone=settings.DEFAULT_ADMIN_PHONE,
                    hash_password=await hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    status=True,
                    password_reset_required=False,
                    email_verified=True,
                )

                db.add(admin_user)
                await db.commit()
                await db.refresh(admin_user)

                role_mapping = RoleMapper(user_id=admin_user.id, role_id=super_role.id)
                db.add(role_mapping)

            await db.commit()
            logger.info("Admin account initialization completed")

        except Exception as e:
            logger.error(f"Failed to create admin account: {str(e)}")
            await db.rollback()
            raise
