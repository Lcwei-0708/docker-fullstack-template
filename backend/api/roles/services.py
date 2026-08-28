from typing import Dict, List, Optional
from models.roles import Roles
from models.role_mapper import RoleMapper
from core.config import settings
from core.rbac import (
    check_user_has_super_role,
    get_user_role_id,
    get_user_role_level,
    is_super_admin_role_name,
    user_has_role,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_
from models.role_attributes import RoleAttributes
from models.role_attributes_mapper import RoleAttributesMapper
from utils.custom_exception import (
    ServerException,
    ConflictException,
    NotFoundException,
    AuthorizationException,
)
from .schema import (
    RoleResponse, RoleCreate, RoleUpdate, RolesListResponse,
    RoleAttributeMappingBatchResponse, AttributeMappingResult,
    RoleAttributesGroupedResponse, RoleAttributesGroup, RoleAttributeDetail,
    PermissionCheckResponse
)

def _ensure_role_is_mutable(role: Roles) -> None:
    """Block mutations of the system super-admin role."""
    if is_super_admin_role_name(role.name):
        raise AuthorizationException("Cannot modify the system super-admin role")

def _to_role_response(role: Roles) -> RoleResponse:
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        level=role.level,
    )

async def _assert_can_manage_role_level(
    db: AsyncSession,
    actor_user_id: str,
    *,
    target_level: int,
    existing_role_level: Optional[int] = None,
) -> int:
    """
    Allow managing roles at the same level or lower.
    Block managing / assigning levels strictly higher than the actor.
    """
    actor_level = await get_user_role_level(actor_user_id, db)
    if existing_role_level is not None and existing_role_level > actor_level:
        raise AuthorizationException(
            "Cannot manage a role with higher level than your own"
        )
    if target_level > actor_level:
        raise AuthorizationException(
            "Cannot assign a role level higher than your own"
        )
    return actor_level

async def _assert_not_own_role(
    db: AsyncSession,
    actor_user_id: str,
    role_id: str,
) -> None:
    """Block editing/deleting the role currently assigned to the actor."""
    if await user_has_role(actor_user_id, role_id, db):
        raise AuthorizationException("Cannot modify or delete your own role")

async def get_all_roles(db: AsyncSession, actor_user_id: str) -> RolesListResponse:
    """Get assignable roles (excludes the system super-admin role)."""
    try:
        actor_level = await get_user_role_level(actor_user_id, db)
        actor_role_id = await get_user_role_id(actor_user_id, db)
        roles_query = (
            select(Roles)
            .where(Roles.name != settings.DEFAULT_SUPER_ADMIN_ROLE)
            .order_by(Roles.level.desc(), Roles.name.asc())
        )
        roles_result = await db.execute(roles_query)
        roles = roles_result.scalars().all()

        role_responses = [_to_role_response(role) for role in roles]
        return RolesListResponse(
            roles=role_responses,
            actor_level=actor_level,
            actor_role_id=actor_role_id,
        )

    except Exception as e:
        raise ServerException(f"Failed to retrieve roles: {str(e)}")

async def create_role(
    db: AsyncSession,
    role_data: RoleCreate,
    actor_user_id: str,
) -> RoleResponse:
    """Create a new role"""
    try:
        if is_super_admin_role_name(role_data.name):
            raise AuthorizationException("Cannot create the system super-admin role")

        await _assert_can_manage_role_level(
            db,
            actor_user_id,
            target_level=role_data.level,
        )

        existing_role = await db.execute(
            select(Roles).where(Roles.name == role_data.name)
        )
        if existing_role.scalar_one_or_none():
            raise ConflictException("Role name already exists")

        role = Roles(
            name=role_data.name,
            description=role_data.description,
            level=role_data.level,
        )
        db.add(role)
        await db.commit()
        await db.refresh(role)

        return _to_role_response(role)

    except (ConflictException, AuthorizationException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to create role: {str(e)}")

async def update_role(
    db: AsyncSession,
    role_id: str,
    role_data: RoleUpdate,
    actor_user_id: str,
) -> RoleResponse:
    """Update role information"""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role not found")

        _ensure_role_is_mutable(role)

        if role_data.name and is_super_admin_role_name(role_data.name):
            raise AuthorizationException("Cannot rename a role to the system super-admin role")

        await _assert_not_own_role(db, actor_user_id, role_id)

        update_data = role_data.model_dump(exclude_unset=True)
        target_level = update_data.get("level", role.level)
        await _assert_can_manage_role_level(
            db,
            actor_user_id,
            target_level=target_level,
            existing_role_level=role.level,
        )

        if role_data.name and role_data.name != role.name:
            existing_role = await db.execute(
                select(Roles).where(Roles.name == role_data.name, Roles.id != role_id)
            )
            if existing_role.scalar_one_or_none():
                raise ConflictException("Role name already exists")

        for field, value in update_data.items():
            setattr(role, field, value)

        await db.commit()
        await db.refresh(role)

        return _to_role_response(role)

    except (ConflictException, NotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to update role: {str(e)}")

async def delete_role(db: AsyncSession, role_id: str, actor_user_id: str) -> bool:
    """Delete a role"""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role not found")

        _ensure_role_is_mutable(role)
        await _assert_not_own_role(db, actor_user_id, role_id)
        await _assert_can_manage_role_level(
            db,
            actor_user_id,
            target_level=role.level,
            existing_role_level=role.level,
        )

        user_count = await db.execute(
            select(func.count(RoleMapper.user_id)).where(RoleMapper.role_id == role_id)
        )
        if user_count.scalar() > 0:
            raise ConflictException("Cannot delete role that is assigned to users")

        await db.execute(
            delete(RoleAttributesMapper).where(RoleAttributesMapper.role_id == role_id)
        )

        await db.execute(
            delete(Roles).where(Roles.id == role_id)
        )
        await db.commit()

        return True

    except (ConflictException, NotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to delete role: {str(e)}")

async def get_role_attribute_mapping(db: AsyncSession, role_id: str) -> RoleAttributesGroupedResponse:
    """Get role attributes mapping grouped by group and category (left join)."""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role not found")

        _ensure_role_is_mutable(role)

        # Use LEFT JOIN to get all attributes and their mappings
        query = select(
            RoleAttributes.name,
            RoleAttributes.group,
            RoleAttributes.category,
            RoleAttributesMapper.value
        ).select_from(
            RoleAttributes
        ).outerjoin(
            RoleAttributesMapper,
            and_(
                RoleAttributes.id == RoleAttributesMapper.attributes_id,
                RoleAttributesMapper.role_id == role_id
            )
        ).order_by(RoleAttributes.id)

        result = await db.execute(query)
        rows = result.all()

        grouped: Dict[str, Dict[str, List[RoleAttributeDetail]]] = {}
        for row in rows:
            group = row.group or "default"
            category = row.category or "uncategorized"
            grouped.setdefault(group, {}).setdefault(category, []).append(
                RoleAttributeDetail(
                    name=row.name,
                    value=row.value if row.value is not None else False,
                )
            )

        groups = []
        for group, categories in grouped.items():
            groups.append(
                RoleAttributesGroup(
                    group=group,
                    categories=categories,
                )
            )

        return RoleAttributesGroupedResponse(groups=groups)

    except (NotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to get role attributes: {str(e)}")

async def update_role_attribute_mapping(
    db: AsyncSession,
    role_id: str,
    attributes_data: Dict[str, bool],
    actor_user_id: str,
) -> RoleAttributeMappingBatchResponse:
    """Batch update role and attributes mapping with detailed results"""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role not found")

        _ensure_role_is_mutable(role)
        await _assert_not_own_role(db, actor_user_id, role_id)
        await _assert_can_manage_role_level(
            db,
            actor_user_id,
            target_level=role.level,
            existing_role_level=role.level,
        )

        results = []
        success_count = 0
        failed_count = 0

        # Get mapping from attribute names to IDs
        attribute_names = list(attributes_data.keys())
        name_to_id_map = {}
        invalid_names = set()

        if attribute_names:
            existing_attributes = await db.execute(
                select(RoleAttributes.id, RoleAttributes.name).where(RoleAttributes.name.in_(attribute_names))
            )
            for row in existing_attributes:
                name_to_id_map[row.name] = row.id

            # Handle invalid attribute names
            invalid_names = set(attribute_names) - set(name_to_id_map.keys())
            for invalid_name in invalid_names:
                results.append(AttributeMappingResult(
                    attribute_id=invalid_name,  # Keep name for error reporting
                    status="failed",
                    message="Invalid attribute name"
                ))
                failed_count += 1

        # Process valid attributes
        for attribute_name, value in attributes_data.items():
            if attribute_name in invalid_names:
                continue

            attribute_id = name_to_id_map.get(attribute_name)
            if not attribute_id:
                continue

            try:
                existing_mapping = await db.execute(
                    select(RoleAttributesMapper).where(
                        and_(
                            RoleAttributesMapper.role_id == role_id,
                            RoleAttributesMapper.attributes_id == attribute_id
                        )
                    )
                )
                mapping = existing_mapping.scalar_one_or_none()

                if mapping:
                    # Update existing mapping
                    mapping.value = value
                else:
                    # Create new mapping
                    new_mapping = RoleAttributesMapper(
                        role_id=role_id,
                        attributes_id=attribute_id,
                        value=value
                    )
                    db.add(new_mapping)

                results.append(AttributeMappingResult(
                    attribute_id=attribute_name,
                    status="success",
                    message="Updated successfully"
                ))
                success_count += 1

            except Exception as e:
                results.append(AttributeMappingResult(
                    attribute_id=attribute_name,
                    status="failed",
                    message=f"Failed to process: {str(e)}"
                ))
                failed_count += 1

        await db.commit()

        return RoleAttributeMappingBatchResponse(
            results=results,
            total_attributes=len(attributes_data),
            success_count=success_count,
            failed_count=failed_count
        )

    except (NotFoundException, AuthorizationException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to update role attributes mapping: {str(e)}")

async def check_user_permissions(
    db: AsyncSession,
    user_id: str,
    required_attributes: List[str] = None
) -> PermissionCheckResponse:
    """Check if user has required permission attributes."""
    try:
        # Get all available attributes
        all_attributes_result = await db.execute(select(RoleAttributes.name))
        all_attributes = [row[0] for row in all_attributes_result.fetchall()]

        if await check_user_has_super_role(user_id, db):
            if required_attributes:
                permissions = {attr: True for attr in required_attributes}
            else:
                permissions = {attr: True for attr in all_attributes}
            return PermissionCheckResponse(permissions=permissions)

        user_role_query = select(RoleMapper.role_id).where(RoleMapper.user_id == user_id)
        user_role_result = await db.execute(user_role_query)
        user_role_id = user_role_result.scalar_one_or_none()

        user_attributes_set = set()
        if user_role_id:
            attributes_query = select(RoleAttributes.name).join(
                RoleAttributesMapper,
                RoleAttributes.id == RoleAttributesMapper.attributes_id
            ).where(
                and_(
                    RoleAttributesMapper.role_id == user_role_id,
                    RoleAttributesMapper.value == True
                )
            )
            attributes_result = await db.execute(attributes_query)
            user_attributes_set = {row[0] for row in attributes_result.fetchall()}

        if not required_attributes:
            permissions = {attr: attr in user_attributes_set for attr in all_attributes}
        else:
            permissions = {attr: attr in user_attributes_set for attr in required_attributes}

        return PermissionCheckResponse(permissions=permissions)

    except Exception as e:
        raise ServerException(f"Failed to check user permissions: {str(e)}")
