import logging
from functools import wraps

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.role_attributes import RoleAttributes
from models.role_attributes_mapper import RoleAttributesMapper
from models.role_mapper import RoleMapper
from models.roles import Roles
from utils.custom_exception import ServerException

logger = logging.getLogger("rbac")


def is_super_admin_role_name(role_name: str | None) -> bool:
    """True when role_name is the ENV-configured system super-admin role."""
    return bool(role_name) and role_name == settings.DEFAULT_SUPER_ADMIN_ROLE


async def get_user_role_level(user_id: str, db: AsyncSession) -> int:
    """Return the user's highest role level, or 0 when the user has no role."""
    try:
        result = await db.execute(
            select(func.max(Roles.level))
            .join(RoleMapper, Roles.id == RoleMapper.role_id)
            .where(RoleMapper.user_id == user_id)
        )
        level = result.scalar_one_or_none()
        return int(level) if level is not None else 0
    except Exception as e:
        raise ServerException(f"Failed to get user role level: {e}")


async def get_user_role_id(user_id: str, db: AsyncSession) -> str | None:
    """Return the user's primary role id (highest level), or None when unassigned."""
    try:
        result = await db.execute(
            select(Roles.id)
            .join(RoleMapper, Roles.id == RoleMapper.role_id)
            .where(RoleMapper.user_id == user_id)
            .order_by(Roles.level.desc(), Roles.name.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        raise ServerException(f"Failed to get user role id: {e}")


async def user_has_role(user_id: str, role_id: str, db: AsyncSession) -> bool:
    """True when the user is currently assigned the given role."""
    try:
        result = await db.execute(
            select(RoleMapper.role_id).where(
                RoleMapper.user_id == user_id,
                RoleMapper.role_id == role_id,
            )
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        raise ServerException(f"Failed to check user role assignment: {e}")


async def get_user_attributes(user_id: str, db: AsyncSession) -> dict[str, bool]:
    """Get user attributes"""
    try:
        # Check if user has super admin role first
        if await check_user_has_super_role(user_id, db):
            # Super admin has all attributes - get all available attributes
            all_attributes_result = await db.execute(select(RoleAttributes.name))
            all_attributes = [row.name for row in all_attributes_result]
            return {attr: True for attr in all_attributes}

        result = await db.execute(
            select(RoleAttributes.name, RoleAttributesMapper.value)
            .join(RoleAttributesMapper, RoleAttributes.id == RoleAttributesMapper.attributes_id)
            .join(RoleMapper, RoleMapper.role_id == RoleAttributesMapper.role_id)
            .where(RoleMapper.user_id == user_id)
        )

        attributes = {}
        for row in result:
            attr_name = row.name
            attr_value = row.value

            if attr_name in attributes:
                attributes[attr_name] = attributes[attr_name] or attr_value
            else:
                attributes[attr_name] = attr_value

        return attributes
    except Exception as e:
        raise ServerException(f"Failed to get user attributes: {e}")


async def check_user_has_super_role(user_id: str, db: AsyncSession) -> bool:
    """Check if user has super admin role"""
    try:
        result = await db.execute(
            select(Roles.name)
            .join(RoleMapper, Roles.id == RoleMapper.role_id)
            .where(RoleMapper.user_id == user_id)
        )

        user_roles = [row.name for row in result]
        return settings.DEFAULT_SUPER_ADMIN_ROLE in user_roles
    except Exception as e:
        raise ServerException(f"Failed to check super role: {e}")


def require_permission(required_attributes: list[str]):
    """Permission check decorator"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = kwargs.get("token")
            db = kwargs.get("db")

            if not db:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            user_id = token.get("sub")

            # Check if user has super admin role first
            if await check_user_has_super_role(user_id, db):
                return await func(*args, **kwargs)

            # If not super admin, check specific permissions
            user_attributes = await get_user_attributes(user_id, db)

            # Convert Permission enum to string value if needed
            def get_attr_value(attr):
                """Convert Permission enum to string value, or return as-is if already a string"""
                if hasattr(attr, "value"):
                    return attr.value
                return str(attr) if attr else attr

            # Check if the user has at least one of the required permissions
            attr_values = [get_attr_value(attr) for attr in required_attributes]
            has_permission = any(
                user_attributes.get(attr_value, False) for attr_value in attr_values
            )

            if not has_permission:
                logger.warning(
                    f"Permission denied for user {user_id}. "
                    f"Required: {attr_values}, "
                    f"User has: {[k for k, v in user_attributes.items() if v]}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
