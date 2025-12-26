from enum import Enum
from datetime import datetime
from core.config import settings
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

class UserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone: str = Field(..., description="Phone number")
    status: bool = Field(..., description="User status")
    created_at: datetime = Field(..., description="User creation time")
    role: Optional[str] = Field(None, description="User role")

class UserPagination(BaseModel):
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of users per page")
    total_pages: int = Field(..., description="Total number of pages")

class UserSortBy(str, Enum):
    FIRST_NAME: str = "first_name"
    LAST_NAME: str = "last_name"
    EMAIL: str = "email"
    PHONE: str = "phone"
    ROLE: str = "role"
    STATUS: str = "status"
    CREATED_AT: str = "created_at"

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    email: EmailStr = Field(..., description="User email address")
    phone: str = Field(..., min_length=1, max_length=20, description="Phone number")
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, max_length=50, description="Password")
    status: bool = Field(True, description="User status")
    role: Optional[str] = Field(None, description="User role")

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Last name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    phone: Optional[str] = Field(None, min_length=1, max_length=20, description="Phone number")
    status: Optional[bool] = Field(None, description="User status")
    role: Optional[str] = Field(None, description="User role")

class UserDelete(BaseModel):
    user_ids: List[str] = Field(..., min_items=1, description="List of user IDs to delete")

class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, max_length=50, description="New password")

class UserDeleteResult(BaseModel):
    user_id: str = Field(..., description="User ID")
    status: str = Field(..., description="Processing status: success, failed", example="success|failed", pattern="^(success|failed)$")
    message: str = Field(..., description="Result message")

class UserDeleteBatchResponse(BaseModel):
    results: List[UserDeleteResult] = Field(..., description="Individual user deletion results")
    total_users: int = Field(..., description="Total number of users processed")
    success_count: int = Field(..., description="Number of successfully deleted users")
    failed_count: int = Field(..., description="Number of failed deletions")

user_delete_success_response_example = {
    "code": 200,
    "message": "All users deleted successfully",
    "data": {
        "results": [
            {
                "user_id": "uuid-user-id-1",
                "status": "success",
                "message": "User deleted successfully"
            },
            {
                "user_id": "uuid-user-id-2",
                "status": "success",
                "message": "User deleted successfully"
            }
        ],
        "total_users": 2,
        "success_count": 2,
        "failed_count": 0
    }
}

user_delete_partial_response_example = {
    "code": 207,
    "message": "Users deleted with partial success",
    "data": {
        "results": [
            {
                "user_id": "uuid-user-id-1",
                "status": "success",
                "message": "User deleted successfully"
            },
            {
                "user_id": "uuid-user-id-2",
                "status": "failed",
                "message": "User not found"
            }
        ],
        "total_users": 2,
        "success_count": 1,
        "failed_count": 1
    }
}

user_delete_failed_response_example = {
    "code": 400,
    "message": "All users failed to delete",
    "data": {
        "results": [
            {
                "user_id": "uuid-user-id-1",
                "status": "failed",
                "message": "User not found"
            }
        ],
        "total_users": 1,
        "success_count": 0,
        "failed_count": 1
    }
}