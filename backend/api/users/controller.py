import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from core.dependencies import get_db
from utils import APIResponse, parse_responses, common_responses
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from .services import get_user, get_users, create_user, update_user, delete_user
from .schema import UserCreate, UserUpdate, UserRead, UserPagination, UserSortField

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])

@router.get(
    "/",
    response_model=APIResponse[UserPagination],
    summary="Get all users",
    responses=parse_responses({
        200: ("Users retrieved successfully", APIResponse[UserPagination]),
        404: ("No users found", APIResponse[None]),
    }, default=common_responses)
)
async def read_users(
    page: int = Query(1, ge=1, description="Page number (default is 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Number of items per page (default is 10)"),
    keyword: Optional[str] = Query(None, description="User name filter (optional)"),
    sort_by: Optional[UserSortField] = Query(None, description="Sort field"),
    desc: bool = Query(False, description="Sort in descending order (default is false)"),
    db: Session = Depends(get_db)
):
    """
    Query users by conditions (pagination, keyword, status, role, sorting)
    """    
    result = get_users(
        db=db,
        page=page,
        per_page=per_page,
        keyword=keyword,
        sort_by=sort_by.value if sort_by else None,
        desc=desc
    )

    if not result["users"]:
        return APIResponse(code=404, message="No users found", data=None)

    return APIResponse(code=200, message="Users retrieved successfully", data=result)

@router.get(
    "/{user_id}",
    response_model=APIResponse[UserRead],
    summary="Get a user by ID",
    responses=parse_responses({
        200: ("User retrieved successfully", APIResponse[UserRead]),
        404: ("User not found", APIResponse[None]),
    }, default=common_responses)
)
async def read_user(
    user_id: int = Path(..., ge=1, description="The ID of the user to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a user by their ID.
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = UserRead.model_validate(user)
    return APIResponse(code=200, message="User retrieved successfully", data=user_data)

@router.post(
    "/",
    response_model=APIResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    responses=parse_responses({
        201: ("User created successfully", APIResponse[UserRead]),
        409: ("User already exists", APIResponse[None]),
    }, default=common_responses)
)
async def create_new_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user with a unique username and email.
    """
    try:
        user = create_user(db, user_in)
        return APIResponse(code=201, message="User created successfully", data=UserRead.model_validate(user))
    except ValueError as e:
        return APIResponse(message=str(e), code=409, data=None)

@router.put(
    "/{user_id}",
    response_model=APIResponse[UserRead],
    summary="Update a user",
    responses=parse_responses({
        200: ("User updated successfully", APIResponse[UserRead]),
        404: ("User not found", APIResponse[None]),
        409: ("Email already exists", APIResponse[None]),
    }, default=common_responses)
)
async def update_existing_user(
    user_id: int = Path(..., ge=1, description="The ID of the user to update"),
    user_in: UserUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Update an existing user's information.
    """
    try:
        user = update_user(db, user_id, user_in)
        if not user:
            return APIResponse(message="User not found", code=404)
        return APIResponse(code=200, message="User updated successfully", data=UserRead.model_validate(user))
    except ValueError as e:
        return APIResponse(message=str(e), code=409)

@router.delete(
    "/{user_id}",
    status_code=200,
    summary="Delete a user",
    responses=parse_responses({
        200: ("User deleted successfully", APIResponse[UserRead]),
        404: ("User not found", APIResponse[None]),
    }, default=common_responses)
)
async def delete_existing_user(
    user_id: int = Path(..., ge=1, description="The ID of the user to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete a user by their ID.
    """
    user = delete_user(db, user_id)
    if not user:
        return APIResponse(message="User not found", code=404)
    return APIResponse(code=200, message="User deleted successfully", data=UserRead.model_validate(user))