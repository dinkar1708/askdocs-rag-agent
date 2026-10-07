"""Pydantic schemas for authentication and user management"""

import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserBase(BaseModel):
    """Base user schema"""
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = None
    role: str = Field(default="user", description="User role: 'admin', 'user', or 'viewer'")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, v_clean):
            raise ValueError("Invalid email format")
        return v_clean


class UserCreate(UserBase):
    """Schema for registering a new user"""
    password: str = Field(..., min_length=8, description="Password (at least 8 characters)")


class UserLogin(BaseModel):
    """Schema for logging in"""
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, v_clean):
            raise ValueError("Invalid email format")
        return v_clean


class UserUpdate(BaseModel):
    """Schema for updating user details"""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for changing account password"""
    old_password: str
    new_password: str = Field(..., min_length=8, description="New password (at least 8 characters)")


class UserResponse(UserBase):
    """Schema for user profile responses"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserListResponse(BaseModel):
    """Schema for listing users"""
    users: List[UserResponse]
    total: int
