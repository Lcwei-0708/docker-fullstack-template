from typing import TypedDict, Optional
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

class ActionRequiredResponse(BaseModel):
    action_type: str = Field(..., description="Action type for frontend routing: 'password_reset' or 'email_verification'")
    token: Optional[str] = Field(default=None, description="Token for the password reset")
    expires_at: Optional[str] = Field(default=None, description="Token expiration time (ISO format)")

class LogoutRequest(BaseModel):
    logout_all: bool = Field(False, description="Whether to logout from all devices")

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, max_length=50, description="New password")

class TokenValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the token is valid")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")

class PasswordResetCooldownResponse(BaseModel):
    cooldown_seconds: int = Field(..., description="Remaining cooldown time in seconds")

class EmailVerificationResponse(BaseModel):
    message: str = Field(..., description="Verification result message")

class EmailVerificationRequiredResponse(BaseModel):
    expires_at: Optional[str] = Field(default=None, description="Token expiration time (ISO format)")

class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to resend verification")

action_required_response_examples = {
    "passwordReset": {
        "summary": "Password reset required",
        "value": {
            "code": 202,
            "message": "Password reset required",
            "data": {
                "action_type": "password_reset",
                "token": "password_reset_token",
                "expires_at": "2024-01-01T12:00:00+00:00"
            }
        }
    },
    "emailVerification": {
        "summary": "Email verification required",
        "value": {
            "code": 202,
            "message": "Email verification required",
            "data": {
                "action_type": "email_verification",
                "token": None,
                "expires_at": "2024-01-01T12:00:00+00:00"
            }
        }
    }
}