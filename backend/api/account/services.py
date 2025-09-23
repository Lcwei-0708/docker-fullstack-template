from typing import Optional
from sqlalchemy import select
from models.users import Users
from .schema import UserUpdate, PasswordChange
from sqlalchemy.ext.asyncio import AsyncSession
from utils.custom_exception import AuthenticationException, ServerException
from core.security import hash_password, verify_password, clear_user_all_sessions

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[Users]:
    """Get user info by id"""
    result = await db.execute(
        select(Users).where(Users.id == user_id)
    )
    return result.scalar_one_or_none()

async def update_user_profile(db: AsyncSession, user_id: str, user_update: UserUpdate) -> Optional[Users]:
    """Update user info (excluding password)"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    if user_update.email and user_update.email != user.email:
        result = await db.execute(
            select(Users).where(Users.email == user_update.email, Users.id != user_id)
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already exists")
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user

async def change_password(db: AsyncSession, user_id: str, password_change: PasswordChange, redis_client=None) -> bool:
    """Change user password"""
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            return False
        
        if not await verify_password(password_change.current_password, user.hash_password):
            raise AuthenticationException("Current password is incorrect")
        
        user.hash_password = await hash_password(password_change.new_password)
        user.password_reset_required = False
        
        if password_change.logout_all_devices and redis_client:
            await clear_user_all_sessions(db, redis_client, user_id)
        
        await db.commit()
        
        return True
    except AuthenticationException:
        raise
    except Exception:
        raise ServerException("Failed to change password")