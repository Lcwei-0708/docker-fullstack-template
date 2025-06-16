from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    email: EmailStr = Field(..., description="User email address")
    phone: str = Field(..., min_length=1, max_length=20, description="Phone number")
    password: str = Field(..., min_length=6, max_length=255, description="Password")

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Last name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    phone: Optional[str] = Field(None, min_length=1, max_length=20, description="Phone number")
    password: Optional[str] = Field(None, min_length=6, max_length=255, description="Password")
    is_active: Optional[bool] = Field(None, description="Is active")

class UserRead(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

class UserPagination(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    users: List[UserRead]

class UserSortField(str, Enum):
    first_name = "first_name"
    last_name = "last_name"
    email = "email"
    phone = "phone"
    is_active = "is_active"
    created_at = "created_at"
    updated_at = "updated_at"