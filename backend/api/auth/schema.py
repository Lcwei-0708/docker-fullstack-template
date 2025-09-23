from typing import TypedDict
from datetime import datetime
from pydantic import BaseModel, EmailStr

class LoginResult(TypedDict):
    user: "UserResponse"
    session_id: str
    access_token: str

class SessionResult(TypedDict):
    session_id: str
    access_token: str

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str

class UserLoginResponse(BaseModel):
    access_token: str
    expires_at: datetime
    user: UserResponse

class TokenResponse(BaseModel):
    access_token: str
    expires_at: datetime

class PasswordResetRequiredResponse(BaseModel):
    reset_token: str
    expires_at: str

class ResetPasswordRequest(BaseModel):
    new_password: str

class TokenValidationResponse(BaseModel):
    is_valid: bool