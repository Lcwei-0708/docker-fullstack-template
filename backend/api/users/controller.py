import logging
from typing import Optional
from sqlalchemy.orm import Session
from core.dependencies import get_db
from fastapi_limiter.depends import RateLimiter
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
        200: ("Users retrieved successfully", UserPagination),
        404: ("No users found", None),
    }, default=common_responses),
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
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
    result = await get_users(
        db=db,
        page=page,
        per_page=per_page,
        keyword=keyword,
        sort_by=sort_by.value if sort_by else None,
        desc=desc
    )

    if not result["users"]:
        raise HTTPException(status_code=404, detail="No users found")

    return APIResponse(code=200, message="Users retrieved successfully", data=result)

@router.get(
    "/{user_id}",
    response_model=APIResponse[UserRead],
    summary="Get a user by ID",
    responses=parse_responses({
        200: ("User retrieved successfully", UserRead),
        404: ("User not found", None),
    }, default=common_responses),
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def read_user(
    user_id: str = Path(..., description="The ID of the user to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a user by their ID.
    """
    user = await get_user(db, user_id)
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
        201: ("User created successfully", UserRead),
        409: ("User already exists", None),
    }, default=common_responses),
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def create_new_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user with a unique username and email.
    """
    try:
        user = await create_user(db, user_in)
        return APIResponse(code=201, message="User created successfully", data=UserRead.model_validate(user))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.put(
    "/{user_id}",
    response_model=APIResponse[UserRead],
    summary="Update a user",
    responses=parse_responses({
        200: ("User updated successfully", UserRead),
        404: ("User not found", None),
        409: ("Email already exists", None),
    }, default=common_responses),
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def update_existing_user(
    user_id: str = Path(..., description="The ID of the user to update"),
    user_in: UserUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Update an existing user's information.
    """
    try:
        user = await update_user(db, user_id, user_in)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return APIResponse(code=200, message="User updated successfully", data=UserRead.model_validate(user))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Delete a user",
    responses=parse_responses({
        204: ("User deleted successfully"),
        404: ("User not found", None),
    }, default=common_responses ),
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def delete_existing_user(
    user_id: str = Path(..., description="The ID of the user to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete a user by their ID.
    """
    user = await delete_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return APIResponse(code=204, message="User deleted successfully")