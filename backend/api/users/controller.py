import redis
from typing import Optional
from core.redis import get_redis
from core.dependencies import get_db
from core.security import verify_token
from core.permissions import Permission
from core.rbac import require_permission
from sqlalchemy.ext.asyncio import AsyncSession
from utils.response import APIResponse, parse_responses, common_responses
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path, Response
from .services import get_all_users, create_user, update_user, delete_users, reset_user_password
from .schema import (
    UserPagination, UserSortBy, UserCreate, UserUpdate, UserDelete, PasswordReset, UserResponse, 
    UserDeleteBatchResponse, user_delete_success_response_example, user_delete_partial_response_example, 
    user_delete_failed_response_example
)
from utils.custom_exception import NotFoundException, ConflictException

router = APIRouter(tags=["Users"])

@router.get(
    "/",
    response_model=APIResponse[UserPagination],
    response_model_exclude_none=True,
    summary="Get all users",
    responses=parse_responses({
        200: ("Successfully retrieved users", UserPagination)
    }, common_responses)
)
@require_permission([Permission.VIEW_USERS, Permission.MANAGE_USERS])
async def get_users(
    request: Request,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
    keyword: Optional[str] = Query(None, description="Keyword to search for users"),
    status: Optional[str] = Query(None, description="Filter user status (multiple values separated by commas, example: true,false)"),
    role: Optional[str] = Query(None, description="Filter user role (multiple values separated by commas, example: admin,manager)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Number of users per page"),
    sort_by: Optional[UserSortBy] = Query(None, description="Sort by field"),
    desc: bool = Query(False, description="Sort order")
):
    try:
        data = await get_all_users(
            db=db,
            keyword=keyword,
            status=status,
            role=role,
            page=page,
            per_page=per_page,
            sort_by=sort_by.value if sort_by else None,
            desc=desc
        )        
        return APIResponse(code=200, message="Successfully retrieved users", data=data)
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/",
    response_model=APIResponse[UserResponse],
    response_model_exclude_none=True,
    summary="Create new user",
    responses=parse_responses({
        200: ("User created successfully", UserResponse)
    }, common_responses)
)
@require_permission([Permission.MANAGE_USERS])
async def create_user_api(
    user_data: UserCreate,
    request: Request,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user account"""
    try:
        user = await create_user(db, user_data)
        return APIResponse(code=200, message="User created successfully", data=user)
    except Exception as e:
        if "Email already exists" in str(e):
            raise HTTPException(status_code=409, detail="Email already exists")
        raise HTTPException(status_code=500)

@router.put(
    "/{user_id}",
    response_model=APIResponse[UserResponse],
    response_model_exclude_none=True,
    summary="Update user info",
    responses=parse_responses({
        200: ("User updated successfully", UserResponse)
    }, common_responses)
)
@require_permission([Permission.MANAGE_USERS])
async def update_user_api(
    request: Request = None,
    token: dict = Depends(verify_token),
    user_id: str = Path(..., description="User ID"),
    user_data: UserUpdate = None,
    db: AsyncSession = Depends(get_db)
):
    """Update user information"""
    try:
        user = await update_user(db, user_id, user_data)
        return APIResponse(code=200, message="User updated successfully", data=user)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except ConflictException:
        raise HTTPException(status_code=409, detail="Email already exists")
    except Exception:
        raise HTTPException(status_code=500)

@router.delete(
    "/",
    response_model=APIResponse[UserDeleteBatchResponse],
    response_model_exclude_none=True,
    summary="Delete users",
    responses=parse_responses({
        200: ("All users deleted successfully", UserDeleteBatchResponse, user_delete_success_response_example),
        207: ("Users deleted with partial success", UserDeleteBatchResponse, user_delete_partial_response_example),
        400: ("All users failed to delete", UserDeleteBatchResponse, user_delete_failed_response_example)
    }, common_responses)
)
@require_permission([Permission.MANAGE_USERS])
async def delete_users_api(
    delete_data: UserDelete,
    request: Request,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Delete multiple users"""
    try:
        batch_result = await delete_users(db, redis_client, delete_data.user_ids)
        
        # Determine response code based on results
        if batch_result.failed_count == 0:
            # All successful
            return APIResponse(
                code=200, 
                message="All users deleted successfully", 
                data=batch_result
            )
        elif batch_result.success_count == 0:
            # All failed - return 400 status code
            response = APIResponse(
                code=400, 
                message="All users failed to delete", 
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
                message="Users deleted with partial success", 
                data=batch_result
            )
            return Response(
                content=response.model_dump_json(),
                status_code=207,
                media_type="application/json"
            )
    except Exception:
        raise HTTPException(status_code=500)

@router.post(
    "/{user_id}/reset-password",
    response_model=APIResponse[dict],
    response_model_exclude_none=True,
    summary="Reset user password",
    responses=parse_responses({
        200: ("Password reset successfully", dict)
    }, common_responses)
)
@require_permission([Permission.MANAGE_USERS])
async def reset_user_password_api(
    user_id: str = Path(..., description="User ID"),
    password_data: PasswordReset = None,
    request: Request = None,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Reset user password and logout all devices"""
    try:
        await reset_user_password(db, redis_client, user_id, password_data.new_password)
        return APIResponse(code=200, message="Password reset successfully and all devices logged out")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception:
        raise HTTPException(status_code=500) 