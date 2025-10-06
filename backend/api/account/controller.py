from core.redis import get_redis
from core.dependencies import get_db
from core.security import verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from .schema import UserProfile, UserUpdate, PasswordChange
from utils.response import APIResponse, parse_responses, common_responses
from .services import get_user_by_id, update_user_profile, change_password
from utils.custom_exception import AuthenticationException, NotFoundException

router = APIRouter(tags=["Account"])

@router.get(
    "/profile",
    response_model=APIResponse[UserProfile],
    summary="Get current user profile",
    responses=parse_responses({
        200: ("User profile retrieved successfully", UserProfile)
    }, common_responses)
)
async def get_user_profile_api(
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current authenticated user's profile information.
    """
    try:
        user_id = token.get("sub")
        user = await get_user_by_id(db, user_id)
        
        if not user:
            raise NotFoundException("User not found")
        
        user_data = UserProfile(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            status=user.status,
            created_at=user.created_at
        )
        
        return APIResponse(code=200, message="User profile retrieved successfully", data=user_data)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception:
        raise HTTPException(status_code=500)

@router.put(
    "/profile",
    response_model=APIResponse[UserProfile],
    response_model_exclude_unset=True,
    summary="Update current user profile",
    responses=parse_responses({
        200: ("User profile updated successfully", UserProfile)
    }, common_responses)
)
async def update_user_profile_api(
    user_update: UserUpdate,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current authenticated user's profile information (excluding password).
    """
    try:
        user_id = token.get("sub")        
        user = await update_user_profile(db, user_id, user_update)
        
        if not user:
            raise NotFoundException("User not found")
        
        user_data = UserProfile(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            status=user.status,
            created_at=user.created_at
        )

        return APIResponse(code=200, message="User profile updated successfully", data=user_data)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except ValueError:
        raise HTTPException(status_code=409, detail="Email already exists")
    except Exception:
        raise HTTPException(status_code=500)

@router.put(
    "/password",
    response_model=APIResponse[None],
    response_model_exclude_unset=True,
    summary="Change current user password",
    responses=parse_responses({
        200: ("Password changed successfully", None),
        401: ("Invalid or expired token / Current password is incorrect", None)
    }, common_responses)
)
async def change_user_password_api(
    password_change: PasswordChange,
    token: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """
    Change the current authenticated user's password.
    """
    try:
        user_id = token.get("sub")
        success = await change_password(db, user_id, password_change, redis_client)
        
        if success:
            return APIResponse(code=200, message="Password changed successfully")
            
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))