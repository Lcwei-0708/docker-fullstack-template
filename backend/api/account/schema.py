from typing import Optional
from datetime import datetime
from core.config import settings
from pydantic import BaseModel, EmailStr, Field, model_validator

class UserProfile(BaseModel):
    id: str = Field(..., description="User ID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="User email address")
    phone: str = Field(..., description="Phone number")
    status: bool = Field(..., description="User status")
    created_at: datetime = Field(..., description="User creation time")

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Last name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    phone: Optional[str] = Field(None, min_length=1, max_length=20, description="Phone number")

class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, max_length=50, description="Current password")
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, max_length=50, description="New password")
    logout_other_devices: bool = Field(True, description="Logout other devices")

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_logout_field(cls, data):
        if isinstance(data, dict) and "logout_other_devices" not in data and "logout_all_devices" in data:
            data = data.copy()
            data["logout_other_devices"] = data.pop("logout_all_devices")
        return data