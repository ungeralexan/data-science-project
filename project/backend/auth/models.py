"""
Pydantic models for authentication.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr

from config import DEFAULT_THEME, DEFAULT_PREFERENCE_LANGUAGE # pylint: disable=import-error

#   This file defines Pydantic models used in the authentication system.

class UserCreate(BaseModel):
    """Model for user registration."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    interest_keys: list[str]
    interest_text: Optional[str] = None  # Optional additional description
    theme_preference: Optional[str] = DEFAULT_THEME  # Default theme is light
    language_preference: str


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
    theme_preference: Optional[str] = None 
    language_preference: Optional[str] = None


class UserResponse(BaseModel):
    """Model for returning user info like profile details without password."""
    user_id: int
    email: str
    first_name: str
    last_name: str
    interest_keys: Optional[list] = None
    interest_text: Optional[str] = None
    suggested_event_ids: Optional[list] = None
    theme_preference: str = DEFAULT_THEME  # User's theme preference
    language_preference: str = DEFAULT_PREFERENCE_LANGUAGE  # User's language preference


class TokenResponse(BaseModel):
    """Model for token response. This is used when returning JWT tokens."""
    access_token: str # JWT Token String
    token_type: str #Always "bearer" (OAuth2 Standard)
    user: UserResponse # User info associated with the token


class PasswordResetRequest(BaseModel):
    """Model for requesting a password reset."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Model for resetting password with token."""
    token: str
    new_password: str
