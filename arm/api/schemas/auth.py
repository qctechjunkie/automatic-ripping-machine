"""
Pydantic Schemas for Authentication API
Defines request/response models for auth endpoints
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ============================================================================
# Token Schemas
# ============================================================================

class Token(BaseModel):
    """JWT access token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Data stored in JWT token"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    is_admin: bool = False


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user fields"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100, description="Password")


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class UserResponse(UserBase):
    """Schema for user responses (without password)"""
    user_id: int
    is_admin: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating user"""
    current_password: str = Field(..., min_length=1, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


# ============================================================================
# Password Reset Schemas
# ============================================================================

class PasswordChangeRequest(BaseModel):
    """Request to change password"""
    current_password: str = Field(..., min_length=1, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100,
                             description="New password (min 8 characters)")
    confirm_password: str = Field(..., min_length=8, max_length=100)

    def passwords_match(self) -> bool:
        """Validate that new passwords match"""
        return self.new_password == self.confirm_password


# ============================================================================
# Response Messages
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    detail: Optional[str] = None
