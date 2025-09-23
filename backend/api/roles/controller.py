from core.dependencies import get_db
from core.security import verify_token
from core.rbac import require_permission
from core.permissions import Permission
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, Path
from utils.response import APIResponse, parse_responses, common_responses
from utils.custom_exception import NotFoundException, ConflictException, ServerException
from .services import (
    get_all_roles, create_role, update_role, delete_role, 
    get_all_role_attributes, create_role_attribute, update_role_attribute, delete_role_attribute,
    get_role_attribute_mapping, update_role_attribute_mapping
)
from .schema import (
    RoleResponse, RoleCreate, RoleUpdate, RolesListResponse, RoleAttributeResponse,
    RoleAttributesListResponse, RoleAttributeCreate, RoleAttributeUpdate,
    RoleAttributesMapping, RoleAttributeMappingBatchResponse
)

router = APIRouter(tags=["Roles"])

@router.get(
    "/",
    response_model=APIResponse[RolesListResponse],
    response_model_exclude_none=True,
    summary="Get all custom roles",
    responses=parse_responses({
        200: ("Successfully retrieved roles", RolesListResponse)
    }, common_responses)
)
@require_permission([Permission.VIEW_ROLES, Permission.MANAGE_ROLES])
async def get_roles(
    request: Request,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all custom roles"""
    try:
        roles = await get_all_roles(db)
        return APIResponse(code=200, message="Successfully retrieved roles", data=roles)
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/",
    response_model=APIResponse[RoleResponse],
    response_model_exclude_none=True,
    summary="Create new role",
    responses=parse_responses({
        200: ("Role created successfully", RoleResponse),
        409: ("Role name already exists", None)
    }, common_responses)
)
@require_permission([Permission.MANAGE_ROLES])
async def create_role_api(
    role_data: RoleCreate,
    request: Request,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new role"""
    try:
        role = await create_role(db, role_data)
        return APIResponse(code=200, message="Role created successfully", data=role)
    except ConflictException:
        raise HTTPException(status_code=409, detail="Role name already exists")
    except Exception:
        raise HTTPException(status_code=500)

@router.put(
    "/{role_id}",
    response_model=APIResponse[RoleResponse],
    response_model_exclude_none=True,
    summary="Update role info",
    responses=parse_responses({
        200: ("Role updated successfully", RoleResponse),
        404: ("Role not found", None),
        409: ("Role name already exists", None)
    }, common_responses)
)
@require_permission([Permission.MANAGE_ROLES])
async def update_role_api(
    role_id: str = Path(..., description="Role ID"),
    role_data: RoleUpdate = None,
    request: Request = None,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Update role information"""
    try:
        role = await update_role(db, role_id, role_data)
        return APIResponse(code=200, message="Role updated successfully", data=role)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Role not found")
    except ConflictException:
        raise HTTPException(status_code=409, detail="Role name already exists")
    except ServerException:
        raise HTTPException(status_code=500)

@router.delete(
    "/{role_id}",
    response_model=APIResponse[dict],
    response_model_exclude_none=True,
    summary="Delete role",
    responses=parse_responses({
        200: ("Role deleted successfully", None),
        404: ("Role not found", None),
        409: ("Cannot delete role that is assigned to users", None)
    }, common_responses)
)
@require_permission([Permission.MANAGE_ROLES])
async def delete_role_api(
    role_id: str = Path(..., description="Role ID"),
    request: Request = None,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Delete a role"""
    try:
        await delete_role(db, role_id)
        return APIResponse(code=200, message="Role deleted successfully")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Role not found")
    except ConflictException:
        raise HTTPException(status_code=409, detail="Cannot delete role that is assigned to users")
    except Exception:
        raise HTTPException(status_code=500)

@router.get(
    "/attributes",
    response_model=APIResponse[RoleAttributesListResponse],
    response_model_exclude_none=True,
    summary="Get all role attributes",
    responses=parse_responses({
        200: ("Successfully retrieved role attributes", RoleAttributesListResponse)
    }, common_responses)
)
@require_permission([Permission.VIEW_ROLES, Permission.MANAGE_ROLES])
async def get_role_attributes_api(
    request: Request,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all available role attributes"""
    try:
        attributes = await get_all_role_attributes(db)
        return APIResponse(code=200, message="Successfully retrieved role attributes", data=attributes)
    except Exception:
        raise HTTPException(status_code=500) 

@router.post(
    "/attributes",
    response_model=APIResponse[RoleAttributeResponse],
    response_model_exclude_none=True,
    summary="Create new role attribute",
    responses=parse_responses({
        200: ("Role attribute created successfully", RoleAttributeResponse),
        409: ("Attribute name already exists", None)
    }, common_responses)
)
@require_permission([Permission.MANAGE_ROLES])
async def create_role_attribute_api(
    attribute_data: RoleAttributeCreate,
    request: Request,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new role attribute"""
    try:
        attribute = await create_role_attribute(db, attribute_data)
        return APIResponse(code=200, message="Role attribute created successfully", data=attribute)
    except ConflictException:
        raise HTTPException(status_code=409, detail="Attribute name already exists")
    except Exception:
        raise HTTPException(status_code=500)

@router.put(
    "/attributes/{attribute_id}",
    response_model=APIResponse[RoleAttributeResponse],
    response_model_exclude_none=True,
    summary="Update role attribute info",
    responses=parse_responses({
        200: ("Role attribute updated successfully", RoleAttributeResponse),
        404: ("Role attribute not found", None),
        409: ("Attribute name already exists", None)
    }, common_responses)
)
@require_permission([Permission.MANAGE_ROLES])
async def update_role_attribute_api(
    attribute_id: str = Path(..., description="Attribute ID"),
    attribute_data: RoleAttributeUpdate = None,
    request: Request = None,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Update role attribute information"""
    try:
        attribute = await update_role_attribute(db, attribute_id, attribute_data)
        return APIResponse(code=200, message="Role attribute updated successfully", data=attribute)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Role attribute not found")
    except ConflictException:
        raise HTTPException(status_code=409, detail="Attribute name already exists")
    except Exception:
        raise HTTPException(status_code=500)

@router.delete(
    "/attributes/{attribute_id}",
    response_model=APIResponse[dict],
    response_model_exclude_none=True,
    summary="Delete role attribute",
    responses=parse_responses({
        200: ("Role attribute deleted successfully", None),
        404: ("Role attribute not found", None),
        409: ("Cannot delete attribute that is assigned to roles", None)
    }, common_responses)
)
@require_permission([Permission.MANAGE_ROLES])
async def delete_role_attribute_api(
    attribute_id: str = Path(..., description="Attribute ID"),
    request: Request = None,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Delete a role attribute"""
    try:
        await delete_role_attribute(db, attribute_id)
        return APIResponse(code=200, message="Role attribute deleted successfully")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Role attribute not found")
    except ConflictException:
        raise HTTPException(status_code=409, detail="Cannot delete attribute that is assigned to roles")
    except Exception:
        raise HTTPException(status_code=500)

@router.get(
    "/{role_id}/attributes",
    response_model=APIResponse[RoleAttributesMapping],
    response_model_exclude_none=True,
    summary="Get role attributes mapping",
    responses=parse_responses({
        200: ("Successfully retrieved role attributes mapping", RoleAttributesMapping, RoleAttributesMapping.get_example_response()),
        404: ("Role not found", None)
    }, common_responses)
)
@require_permission([Permission.VIEW_ROLES, Permission.MANAGE_ROLES])
async def get_role_attribute_mapping_api(
    role_id: str = Path(..., description="Role ID"),
    request: Request = None,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get role attributes mapping with all available attributes"""
    try:
        attributes_mapping = await get_role_attribute_mapping(db, role_id)
        return APIResponse(
            code=200, 
            message="Successfully retrieved role attributes mapping", 
            data=attributes_mapping
        )
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Role not found")
    except Exception:
        raise HTTPException(status_code=500)

@router.put(
    "/{role_id}/attributes",
    response_model=APIResponse[RoleAttributeMappingBatchResponse],
    response_model_exclude_none=True,
    summary="Update role attributes",
    responses=parse_responses({
        200: ("All role attributes processed successfully", RoleAttributeMappingBatchResponse),
        207: ("Role attributes processed with partial success", RoleAttributeMappingBatchResponse),
        400: ("All role attributes failed to process", RoleAttributeMappingBatchResponse)
    }, common_responses)
)
@require_permission([Permission.MANAGE_ROLES])
async def update_role_attribute_mapping_api(
    role_id: str = Path(..., description="Role ID"),
    attributes_data: RoleAttributesMapping = None,
    request: Request = None,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Update role attributes with batch processing results"""
    try:
        batch_result = await update_role_attribute_mapping(db, role_id, attributes_data.attributes)
        
        # Determine response code based on results
        if batch_result.failed_count == 0:
            # All successful
            return APIResponse(
                code=200, 
                message="All role attributes processed successfully", 
                data=batch_result
            )
        elif batch_result.success_count == 0:
            # All failed
            return APIResponse(
                code=400, 
                message="All role attributes failed to process", 
                data=batch_result
            )
        else:
            # Partial success
            return APIResponse(
                code=207, 
                message="Role attributes processed with partial success", 
                data=batch_result
            )
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Role not found")
    except Exception:
        raise HTTPException(status_code=500)