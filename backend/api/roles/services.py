from typing import List, Dict, Optional
from models.roles import Roles
from sqlalchemy import select, func, delete, and_
from models.role_attributes import RoleAttributes
from sqlalchemy.ext.asyncio import AsyncSession
from models.role_attributes_mapper import RoleAttributesMapper
from utils.custom_exception import ServerException, ConflictException, NotFoundException
from .schema import (
    RoleResponse, RoleCreate, RoleUpdate, 
    RoleAttributeResponse, RoleAttributeCreate, RoleAttributeUpdate,
    RoleAttributesMapping, RoleAttributeMappingBatchResponse, AttributeMappingResult
)

async def get_all_roles(db: AsyncSession) -> List[RoleResponse]:
    """Get all roles"""
    try:
        roles_query = select(Roles)
        roles_result = await db.execute(roles_query)
        roles = roles_result.scalars().all()
        
        role_responses = []
        for role in roles:
            role_response = RoleResponse(
                id=role.id,
                name=role.name,
                description=role.description
            )
            role_responses.append(role_response)
        
        return role_responses
        
    except Exception as e:
        raise ServerException(f"Failed to retrieve roles: {str(e)}")

async def create_role(db: AsyncSession, role_data: RoleCreate) -> RoleResponse:
    """Create a new role"""
    try:
        existing_role = await db.execute(
            select(Roles).where(Roles.name == role_data.name)
        )
        if existing_role.scalar_one_or_none():
            raise ConflictException("Role name already exists")
        
        role = Roles(
            name=role_data.name,
            description=role_data.description
        )
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description
        )
        
    except ConflictException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to create role: {str(e)}")

async def update_role(db: AsyncSession, role_id: str, role_data: RoleUpdate) -> RoleResponse:
    """Update role information"""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role not found")
        
        if role_data.name and role_data.name != role.name:
            existing_role = await db.execute(
                select(Roles).where(Roles.name == role_data.name, Roles.id != role_id)
            )
            if existing_role.scalar_one_or_none():
                raise ConflictException("Role name already exists")
        
        update_data = role_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)
        
        await db.commit()
        await db.refresh(role)
        
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description
        )
        
    except (ConflictException, NotFoundException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to update role: {str(e)}")

async def delete_role(db: AsyncSession, role_id: str) -> bool:
    """Delete a role"""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role not found")
        
        from models.role_mapper import RoleMapper
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
        
    except (ConflictException, NotFoundException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to delete role: {str(e)}")

async def get_all_role_attributes(db: AsyncSession) -> List[RoleAttributeResponse]:
    """Get all available role attributes"""
    try:
        attributes_query = select(RoleAttributes)
        attributes_result = await db.execute(attributes_query)
        attributes = attributes_result.scalars().all()
        
        return [
            RoleAttributeResponse(
                id=attr.id,
                name=attr.name,
                description=attr.description
            )
            for attr in attributes
        ]
        
    except Exception as e:
        raise ServerException(f"Failed to retrieve role attributes: {str(e)}")

async def create_role_attribute(db: AsyncSession, attribute_data: RoleAttributeCreate) -> RoleAttributeResponse:
    """Create a new role attribute"""
    try:
        existing_attribute = await db.execute(
            select(RoleAttributes).where(RoleAttributes.name == attribute_data.name)
        )
        if existing_attribute.scalar_one_or_none():
            raise ConflictException("Attribute name already exists")
        
        attribute = RoleAttributes(
            name=attribute_data.name,
            description=attribute_data.description
        )
        db.add(attribute)
        await db.commit()
        await db.refresh(attribute)
        
        return RoleAttributeResponse(
            id=attribute.id,
            name=attribute.name,
            description=attribute.description
        )
        
    except ConflictException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to create role attribute: {str(e)}")

async def update_role_attribute(db: AsyncSession, attribute_id: str, attribute_data: RoleAttributeUpdate) -> RoleAttributeResponse:
    """Update role attribute information"""
    try:
        attribute_result = await db.execute(
            select(RoleAttributes).where(RoleAttributes.id == attribute_id)
        )
        attribute = attribute_result.scalar_one_or_none()
        if not attribute:
            raise NotFoundException("Role attribute not found")
        
        if attribute_data.name and attribute_data.name != attribute.name:
            existing_attribute = await db.execute(
                select(RoleAttributes).where(RoleAttributes.name == attribute_data.name, RoleAttributes.id != attribute_id)
            )
            if existing_attribute.scalar_one_or_none():
                raise ConflictException("Attribute name already exists")
        
        update_data = attribute_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(attribute, field, value)
        
        await db.commit()
        await db.refresh(attribute)
        
        return RoleAttributeResponse(
            id=attribute.id,
            name=attribute.name,
            description=attribute.description
        )
        
    except (ConflictException, NotFoundException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to update role attribute: {str(e)}")

async def delete_role_attribute(db: AsyncSession, attribute_id: str) -> bool:
    """Delete a role attribute"""
    try:
        attribute_result = await db.execute(
            select(RoleAttributes).where(RoleAttributes.id == attribute_id)
        )
        attribute = attribute_result.scalar_one_or_none()
        if not attribute:
            raise NotFoundException("Role attribute not found")
        
        # Check if attribute is assigned to any roles
        mapping_count = await db.execute(
            select(func.count(RoleAttributesMapper.role_id)).where(RoleAttributesMapper.attributes_id == attribute_id)
        )
        if mapping_count.scalar() > 0:
            raise ConflictException("Cannot delete attribute that is assigned to roles")
        
        await db.execute(
            delete(RoleAttributesMapper).where(RoleAttributesMapper.attributes_id == attribute_id)
        )
        
        await db.execute(
            delete(RoleAttributes).where(RoleAttributes.id == attribute_id)
        )
        await db.commit()
        
        return True
        
    except (ConflictException, NotFoundException):
        raise
    except Exception as e:
        raise ServerException(f"Failed to delete role attribute: {str(e)}")

async def get_role_attribute_mapping(db: AsyncSession, role_id: str) -> RoleAttributesMapping:
    """Get role attributes mapping with all available attributes (left join)"""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role not found")
        
        # Use LEFT JOIN to get all attributes and their mappings
        query = select(
            RoleAttributes.id,
            RoleAttributes.name,
            RoleAttributesMapper.value
        ).select_from(
            RoleAttributes
        ).outerjoin(
            RoleAttributesMapper, 
            and_(
                RoleAttributes.id == RoleAttributesMapper.attributes_id,
                RoleAttributesMapper.role_id == role_id
            )
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        attributes_dict = {}
        for row in rows:
            # If value is None (no mapping), set to False
            attributes_dict[row.id] = row.value if row.value is not None else False
        
        return RoleAttributesMapping(attributes=attributes_dict)
        
    except NotFoundException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to get role attributes: {str(e)}")

async def update_role_attribute_mapping(db: AsyncSession, role_id: str, attributes_data: Dict[str, bool]) -> RoleAttributeMappingBatchResponse:
    """Batch update role and attributes mapping with detailed results"""
    try:
        role_result = await db.execute(
            select(Roles).where(Roles.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role not found")
        
        results = []
        success_count = 0
        failed_count = 0
        
        # Validate all attribute IDs are valid first
        attribute_ids = list(attributes_data.keys())
        invalid_ids = set()
        
        if attribute_ids:
            existing_attributes = await db.execute(
                select(RoleAttributes.id).where(RoleAttributes.id.in_(attribute_ids))
            )
            existing_ids = {row[0] for row in existing_attributes.fetchall()}
            invalid_ids = set(attribute_ids) - existing_ids
            
            # Handle invalid attribute IDs
            for invalid_id in invalid_ids:
                results.append(AttributeMappingResult(
                    attribute_id=invalid_id,
                    status="failed",
                    message="Invalid attribute ID"
                ))
                failed_count += 1
        
        # Process valid attributes
        for attribute_id, value in attributes_data.items():
            if attribute_id in invalid_ids:
                continue  # Skip invalid IDs
                
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
                    attribute_id=attribute_id,
                    status="success",
                    message="Updated successfully"
                ))
                success_count += 1
                
            except Exception as e:
                results.append(AttributeMappingResult(
                    attribute_id=attribute_id,
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
        
    except NotFoundException:
        raise
    except Exception as e:
        raise ServerException(f"Failed to update role attributes mapping: {str(e)}")