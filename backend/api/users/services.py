import redis
import logging
from models.users import Users
from models.roles import Roles
from typing import Optional, List
from models.role_mapper import RoleMapper
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from core.security import hash_password, clear_user_all_sessions
from .schema import UserResponse, UserPagination, UserCreate, UserUpdate
from utils.custom_exception import ServerException, ConflictException, NotFoundException

logger = logging.getLogger(__name__)

async def get_all_users(
    db: AsyncSession,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: Optional[str] = None,
    desc: bool = False
) -> UserPagination:
    """Get all users list"""
    try:
        query = select(Users)
        
        if keyword:
            query = query.where(
                or_(
                    Users.first_name.ilike(f"%{keyword}%"),
                    Users.last_name.ilike(f"%{keyword}%"),
                    Users.email.ilike(f"%{keyword}%")
                )
            )
        
        if status:
            status_list = [s.strip().lower() == 'true' for s in status.split(',')]
            if len(status_list) == 1:
                query = query.where(Users.status == status_list[0])
            else:
                query = query.where(Users.status.in_(status_list))
        
        if role:
            role_list = [r.strip() for r in role.split(',')]
            query = query.join(RoleMapper, Users.id == RoleMapper.user_id)
            query = query.join(Roles, RoleMapper.role_id == Roles.id)
            query = query.where(Roles.name.in_(role_list))
        
        if sort_by:
            sort_column = getattr(Users, sort_by, None)
            if sort_column:
                if desc:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Users.created_at.desc())
        
        count_query = select(func.count(Users.id))
        if keyword:
            count_query = count_query.where(
                or_(
                    Users.first_name.ilike(f"%{keyword}%"),
                    Users.last_name.ilike(f"%{keyword}%"),
                    Users.email.ilike(f"%{keyword}%")
                )
            )
        if status:
            status_list = [s.strip().lower() == 'true' for s in status.split(',')]
            if len(status_list) == 1:
                count_query = count_query.where(Users.status == status_list[0])
            else:
                count_query = count_query.where(Users.status.in_(status_list))
        if role:
            role_list = [r.strip() for r in role.split(',')]
            count_query = count_query.join(RoleMapper, Users.id == RoleMapper.user_id)
            count_query = count_query.join(Roles, RoleMapper.role_id == Roles.id)
            count_query = count_query.where(Roles.name.in_(role_list))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        if not users:
            return UserPagination(
                users=[],
                total=0,
                page=page,
                per_page=per_page,
                total_pages=0
            )
        
        user_responses = []
        for user in users:
            role_query = select(Roles.name).join(
                RoleMapper, Roles.id == RoleMapper.role_id
            ).where(RoleMapper.user_id == user.id).limit(1)
            
            role_result = await db.execute(role_query)
            user_role = role_result.scalar()
            
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                status=user.status,
                created_at=user.created_at,
                role=user_role
            )
            user_responses.append(user_response)
        
        total_pages = (total + per_page - 1) // per_page
        
        return UserPagination(
            users=user_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception:
        raise ServerException("Failed to retrieve users")

async def create_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
    """Create a new user"""
    try:
        # Check if the email already exists
        result = await db.execute(
            select(Users).where(Users.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ConflictException("Email already exists")
        
        user = Users(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            hash_password=await hash_password(user_data.password),
            status=user_data.status
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        user_role = None
        if user_data.role:
            await _assign_user_role(db, user.id, user_data.role)
            user_role = user_data.role
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            status=user.status,
            created_at=user.created_at,
            role=user_role
        )
        
    except ConflictException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to create user: {str(e)}")

async def update_user(db: AsyncSession, user_id: str, user_data: UserUpdate) -> UserResponse:
    """Update user information"""
    try:
        result = await db.execute(
            select(Users).where(Users.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")
        
        # Check if the email is already used by another user
        if user_data.email and user_data.email != user.email:
            result = await db.execute(
                select(Users).where(Users.email == user_data.email, Users.id != user_id)
            )
            if result.scalar_one_or_none():
                raise ConflictException("Email already exists")
        
        update_data = user_data.model_dump(exclude_unset=True, exclude={'role'})
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        if 'role' in user_data.model_dump(exclude_unset=True):
            await _update_user_role(db, user_id, user_data.role)
        
        role_query = select(Roles.name).join(
            RoleMapper, Roles.id == RoleMapper.role_id
        ).where(RoleMapper.user_id == user.id).limit(1)
        
        role_result = await db.execute(role_query)
        user_role = role_result.scalar()
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            status=user.status,
            created_at=user.created_at,
            role=user_role
        )
        
    except (ConflictException, NotFoundException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to update user: {str(e)}")

async def delete_users(db: AsyncSession, user_ids: List[str]) -> bool:
    """Delete multiple users"""
    try:
        result = await db.execute(
            select(Users.id).where(Users.id.in_(user_ids))
        )
        existing_ids = result.scalars().all()
        
        if len(existing_ids) != len(user_ids):
            missing_ids = set(user_ids) - set(existing_ids)
            raise NotFoundException(f"Users not found: {', '.join(missing_ids)}")
        
        await db.execute(
            delete(Users).where(Users.id.in_(user_ids))
        )
        await db.commit()
        
        return True
        
    except NotFoundException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to delete users: {str(e)}")

async def reset_user_password(
    db: AsyncSession, 
    redis_client: redis.Redis, 
    user_id: str, 
    new_password: str
) -> bool:
    """Reset user password and logout all devices"""
    try:
        result = await db.execute(
            select(Users).where(Users.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")
        
        user.hash_password = await hash_password(new_password)
        user.password_reset_required = True
        await db.commit()
        
        await clear_user_all_sessions(db, redis_client, user_id)
        
        return True
        
    except NotFoundException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to reset password: {str(e)}")

async def _assign_user_role(db: AsyncSession, user_id: str, role_name: str) -> None:
    """Assign a role to a user"""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.name == role_name)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException(f"Role '{role_name}' not found")
        
        existing_mapping = await db.execute(
            select(RoleMapper).where(
                RoleMapper.user_id == user_id,
                RoleMapper.role_id == role.id
            )
        )
        if existing_mapping.scalar_one_or_none():
            return
        
        role_mapping = RoleMapper(
            user_id=user_id,
            role_id=role.id
        )
        db.add(role_mapping)
        await db.commit()
        
    except NotFoundException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to assign role: {str(e)}")

async def _update_user_role(db: AsyncSession, user_id: str, role_name: Optional[str]) -> None:
    """Update user role (remove existing and assign new one)"""
    try:
        await db.execute(
            delete(RoleMapper).where(RoleMapper.user_id == user_id)
        )
        
        if role_name:
            await _assign_user_role(db, user_id, role_name)
        
        await db.commit()
        
    except Exception as e:
        raise ServerException(f"Failed to update user role: {str(e)}")