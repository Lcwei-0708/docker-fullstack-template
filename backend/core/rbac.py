import logging
from typing import List, Dict, Any
from functools import wraps
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from core.security import verify_token
from models.users import Users
from models.role_mapper import RoleMapper
from models.role_attributes_mapper import RoleAttributesMapper
from models.role_attributes import RoleAttributes

logger = logging.getLogger(__name__)

async def get_user_attributes(
    user_id: str,
    db: AsyncSession
) -> Dict[str, bool]:
    """Get user attributes"""
    try:
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
        logger.error(f"Failed to get user attributes: {e}")
        return {}

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
            user_attributes = await get_user_attributes(user_id, db)

            # Check if the user has all the required permissions
            missing_permissions = []
            for attr in required_attributes:
                if not user_attributes.get(attr, False):
                    missing_permissions.append(attr)
            
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator