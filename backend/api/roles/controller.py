from core.dependencies import get_db
from core.security import verify_token
from core.rbac import require_permission
from core.permissions import Permission
from sqlalchemy.ext.asyncio import AsyncSession
from utils.response import APIResponse, parse_responses, common_responses
from fastapi import APIRouter, Depends, HTTPException, Request, Path, Response
from utils.custom_exception import NotFoundException, ConflictException, ServerException
from .services import (
    get_all_roles, create_role, update_role, delete_role, 
    get_role_attribute_mapping, update_role_attribute_mapping,
    check_user_permissions
)
from .schema import (
    RoleResponse, RoleCreate, RoleUpdate, RolesListResponse,
    RoleAttributesMapping, RoleAttributeMappingBatchResponse,
    RoleAttributesGroupedResponse,
    PermissionCheckResponse,
    role_attributes_success_response_example, role_attributes_partial_response_example, 
    role_attributes_failed_response_example
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
    "/{role_id}/attributes",
    response_model=APIResponse[RoleAttributesGroupedResponse],
    response_model_exclude_none=True,
    summary="Get role attributes mapping",
    responses=parse_responses({
        200: ("Successfully retrieved role attributes mapping", RoleAttributesGroupedResponse, RoleAttributesGroupedResponse.get_example_response()),
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
        200: ("All role attributes processed successfully", RoleAttributeMappingBatchResponse, role_attributes_success_response_example),
        207: ("Role attributes processed with partial success", RoleAttributeMappingBatchResponse, role_attributes_partial_response_example),
        400: ("All role attributes failed to process", RoleAttributeMappingBatchResponse, role_attributes_failed_response_example)
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
            # All failed - return 400 status code
            response = APIResponse(
                code=400, 
                message="All role attributes failed to process", 
                data=batch_result
            )
            return Response(
                content=response.model_dump_json(),
                status_code=400,
                media_type="application/json"
            )
        else:
            # Partial success - return 207 status code
            response = APIResponse(
                code=207, 
                message="Role attributes processed with partial success", 
                data=batch_result
            )
            return Response(
                content=response.model_dump_json(),
                status_code=207,
                media_type="application/json"
            )
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Role not found")
    except Exception:
        raise HTTPException(status_code=500)

@router.get(
    "/permissions",
    response_model=APIResponse[PermissionCheckResponse],
    response_model_exclude_none=True,
    summary="Get current user permissions",
    responses=parse_responses({
        200: ("User permissions retrieved", PermissionCheckResponse, PermissionCheckResponse.get_example_response())
    }, common_responses)
)
async def get_user_permissions_api(
    request: Request = None,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions for the current user"""
    try:
        user_id = token.get("sub")
        result = await check_user_permissions(db, user_id, None)
        
        return APIResponse(code=200, message="User permissions retrieved", data=result)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500)