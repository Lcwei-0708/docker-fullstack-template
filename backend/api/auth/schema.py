from typing import TypedDict
from datetime import datetime
from core.config import settings
from pydantic import BaseModel, EmailStr, Field

class LoginResult(TypedDict):
    user: "UserResponse"
    session_id: str = Field(..., description="Session ID")
    access_token: str = Field(..., description="JWT access token")

class SessionResult(TypedDict):
    session_id: str = Field(..., description="Session ID")
    access_token: str = Field(..., description="JWT access token")

class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    email: EmailStr = Field(..., description="User email address")
    phone: str = Field(..., min_length=1, max_length=20, description="Phone number")
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, max_length=50, description="Password")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="Password")

class UserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: str = Field(..., description="User email address")
    phone: str = Field(..., description="Phone number")

class UserLoginResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    expires_at: datetime = Field(..., description="Token expiration time")
    user: UserResponse = Field(..., description="User information")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    expires_at: datetime = Field(..., description="Token expiration time")

class PasswordResetRequiredResponse(BaseModel):
    reset_token: str = Field(..., description="Password reset token")
    expires_at: str = Field(..., description="Token expiration time")

class LogoutRequest(BaseModel):
    logout_all: bool = Field(False, description="Whether to logout from all devices")

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, max_length=50, description="New password")

class TokenValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the token is valid")