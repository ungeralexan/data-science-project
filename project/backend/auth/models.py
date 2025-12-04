"""
Pydantic models for authentication.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Model for user registration."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Model for updating user information."""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    interest_keys: Optional[list[str]] = None
    interest_text: Optional[str] = None


class UserResponse(BaseModel):
    """Model for user response (excludes password)."""
    user_id: int
    email: str
    first_name: str
    last_name: str
    interest_keys: Optional[list] = None
    interest_text: Optional[str] = None
    suggested_event_ids: Optional[list] = None


class TokenResponse(BaseModel):
    """Model for token response."""
    access_token: str
    token_type: str
    user: UserResponse


class PasswordResetRequest(BaseModel):
    """Model for requesting a password reset."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Model for resetting password with token."""
    token: str
    new_password: str
