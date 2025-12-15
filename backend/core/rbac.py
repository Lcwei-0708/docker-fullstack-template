import logging
from functools import wraps
from typing import List, Dict
from sqlalchemy import select
from models.roles import Roles
from core.config import settings
from fastapi import HTTPException, status
from models.role_mapper import RoleMapper
from sqlalchemy.ext.asyncio import AsyncSession
from models.role_attributes import RoleAttributes
from utils.custom_exception import ServerException
from models.role_attributes_mapper import RoleAttributesMapper

logger = logging.getLogger(__name__)

async def get_user_attributes(user_id: str, db: AsyncSession) -> Dict[str, bool]:
    """Get user attributes"""
    try:
        # Check if user has super admin role first
        if await check_user_has_super_role(user_id, db):
            # Super admin has all attributes - get all available attributes
            all_attributes_result = await db.execute(select(RoleAttributes.name))
            all_attributes = [row.name for row in all_attributes_result]
            return {attr: True for attr in all_attributes}
        
        result = await db.execute(
            select(
                RoleAttributes.name,
                RoleAttributesMapper.value
            )
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
        ServerException(f"Failed to get user attributes: {e}")
        return {}

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
        logger.error(f"Failed to check super role: {e}")
        return False

def require_permission(required_attributes: List[str]):
    """Permission check decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = kwargs.get('token')
            db = kwargs.get('db')
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            user_id = token.get("sub")
            
            # Check if user has super admin role first
            if await check_user_has_super_role(user_id, db):
                return await func(*args, **kwargs)
            
            # If not super admin, check specific permissions
            user_attributes = await get_user_attributes(user_id, db)

            # Check if the user has all the required permissions
            missing_permissions = []
            for attr in required_attributes:
                if not user_attributes.get(attr, False):
                    missing_permissions.append(attr)
            
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator