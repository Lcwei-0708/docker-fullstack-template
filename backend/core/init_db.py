import logging
from sqlalchemy import select
from models.users import Users
from models.roles import Roles
from core.config import settings
from core.security import hash_password
from models.role_mapper import RoleMapper
from core.database import AsyncSessionLocal
from core.permissions import get_attributes
from models.role_attributes import RoleAttributes
from models.role_attributes_mapper import RoleAttributesMapper

logger = logging.getLogger("init_db")

async def init_database():
    """Initialize database with default data: role attributes, roles and admin account"""
    try:
        logger.info("Starting database initialization...")
        
        await create_role_attributes()
        await create_default_roles()
        await assign_super_admin_attributes()
        await create_default_admin()
        
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

async def create_role_attributes():
    """Create role attributes"""
    async with AsyncSessionLocal() as db:
        try:
            attributes = get_attributes()
            created_count = 0
            
            for attr_config in attributes:
                existing_attr = await db.execute(
                    select(RoleAttributes).where(RoleAttributes.name == attr_config["name"])
                )
                if existing_attr.scalar_one_or_none():
                    continue
                
                attribute = RoleAttributes(
                    name=attr_config["name"],
                    description=attr_config["description"]
                )
                db.add(attribute)
                created_count += 1
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create role attributes: {str(e)}")
            await db.rollback()
            raise

async def create_default_roles():
    """Create default roles"""
    async with AsyncSessionLocal() as db:
        try:
            # Get the super admin role name from settings
            super_admin_role_name = settings.DEFAULT_SUPER_ADMIN_ROLE
            
            default_roles = [
                {
                    "name": super_admin_role_name,
                    "description": "Super administrator role with full system access"
                },
                {
                    "name": "user",
                    "description": "Regular user role with basic permissions"
                }
            ]
            
            # Only add "admin" role if it's different from super admin role
            if super_admin_role_name != "admin":
                default_roles.insert(1, {
                    "name": "admin",
                    "description": "Administrator role with most management permissions"
                })
            
            created_count = 0
            
            for role_config in default_roles:
                existing_role = await db.execute(
                    select(Roles).where(Roles.name == role_config["name"])
                )
                if existing_role.scalar_one_or_none():
                    continue
                
                role = Roles(
                    name=role_config["name"],
                    description=role_config["description"]
                )
                db.add(role)
                created_count += 1
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create roles: {str(e)}")
            await db.rollback()
            raise

async def assign_super_admin_attributes():
    """Assign all attributes to super admin role"""
    async with AsyncSessionLocal() as db:
        try:
            # Get super admin role
            super_role_result = await db.execute(
                select(Roles).where(Roles.name == settings.DEFAULT_SUPER_ADMIN_ROLE)
            )
            super_role = super_role_result.scalar_one_or_none()
            
            if not super_role:
                logger.warning(f"Super admin role '{settings.DEFAULT_SUPER_ADMIN_ROLE}' not found, skipping attribute assignment")
                return
            
            # Get all attributes
            attributes_result = await db.execute(select(RoleAttributes))
            all_attributes = attributes_result.scalars().all()
            
            if not all_attributes:
                logger.warning("No role attributes found, skipping attribute assignment")
                return
            
            # Check existing mappings
            existing_mappings_result = await db.execute(
                select(RoleAttributesMapper).where(RoleAttributesMapper.role_id == super_role.id)
            )
            existing_mappings = {mapping.attributes_id for mapping in existing_mappings_result.scalars().all()}
            
            assigned_count = 0
            for attribute in all_attributes:
                if attribute.id in existing_mappings:
                    continue
                
                attribute_mapping = RoleAttributesMapper(
                    role_id=super_role.id,
                    attributes_id=attribute.id,
                    value=True
                )
                db.add(attribute_mapping)
                assigned_count += 1
            
            if assigned_count > 0:
                await db.commit()
                logger.info(f"Assigned {assigned_count} attributes to super admin role")
            else:
                logger.info("Super admin role already has all attributes assigned")
            
        except Exception as e:
            logger.error(f"Failed to assign super admin attributes: {str(e)}")
            await db.rollback()
            raise

async def create_default_admin():
    """Create default admin account"""
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
                logger.info(f"Super admin users already exist: {[user.email for user in existing_super_users]}")
                await db.commit()
                return
            
            existing_user_result = await db.execute(
                select(Users).where(Users.email == settings.DEFAULT_ADMIN_EMAIL)
            )
            existing_user = existing_user_result.scalar_one_or_none()
            
            if existing_user:
                existing_role_mapping = await db.execute(
                    select(RoleMapper).where(
                        RoleMapper.user_id == existing_user.id,
                        RoleMapper.role_id == super_role.id
                    )
                )
                if not existing_role_mapping.scalar_one_or_none():
                    role_mapping = RoleMapper(
                        user_id=existing_user.id,
                        role_id=super_role.id
                    )
                    db.add(role_mapping)
                    logger.info(f"Assigned super admin role to existing user: {existing_user.email}")
            else:
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
                
                role_mapping = RoleMapper(
                    user_id=admin_user.id,
                    role_id=super_role.id
                )
                db.add(role_mapping)
            
            await db.commit()
            logger.info("Admin account initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to create admin account: {str(e)}")
            await db.rollback()
            raise