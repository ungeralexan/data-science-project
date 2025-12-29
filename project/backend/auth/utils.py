"""
Authentication utilities: password hashing, JWT handling, and auth dependencies.
"""
from typing import Optional
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from data.database.database_events import SessionLocal, UserORM  # pylint: disable=import-error
from config import (  # pylint: disable=import-error
    DEFAULT_THEME,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_DAYS,
    PASSWORD_RESET_EXPIRE_HOURS,
    DEFAULT_PREFERENCE_LANGUAGE,
)

from .models import UserResponse

# 
#   This file contains utility functions for authentication,
#   including password hashing, JWT token creation and decoding,
#   and user retrieval from tokens.
#

# Security scheme for FastAPI dependencies. This extracts the Authorization header.
security = HTTPBearer(auto_error=False)


# ----- Password hashing utilities -----
def hash_password(password: str) -> str:
    """Hash a password using bcrypt. (Returns decoded string)"""

    # haspw function is used to hash the password with a generated salt
    # gensalt function generates a random salt for hashing. 
    # A salt is random data that is used as an additional input to a one-way function that "hashes" a password.
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash. (Decodes hash to str for comparison)"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ----- JWT utilities -----
def create_access_token(user_id: int) -> str:
    """Create a JWT access token. This is used for authenticating users."""

    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }

    # jwt.encode() does this:
    #   1. Takes the payload dictionary
    #   2. Converts it to JSON
    #   3. Base64-encodes it (header + payload)
    #   4. Creates a signature using JWT_SECRET_KEY and HS256 algorithm
    #   5. Returns "header.payload.signature" as the JWT token
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """Decode a JWT access token and return the user_id."""

    # jwt.decode() does this:
    #   1. Splits the token into header, payload, and signature
    #   2. Recalculates the signature using JWT_SECREC_KEY
    #   3. Compares calculated signature with the one in the token
    #   4. If they match -> Token is valid
    #   5. Checks if "exp" (expiration) has passed
    #   6. Returns the payload as a dictionary

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create a JWT token for password reset."""

    # Set expiration time for password reset token
    expire = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)

    # Payload includes the email and token type
    payload = {
        "sub": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "password_reset"
    }

    # Create and return the JWT token
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_password_reset_token(token: str) -> Optional[str]:
    """Decode a password reset token and return the email."""
    try:

        # Decode the token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Ensure the token is indeed a password reset token
        if payload.get("type") != "password_reset":
            return None
        
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ----- User ORM to Response conversion -----
def user_orm_to_response(user: UserORM) -> UserResponse:
    """
    Converts a UserORM (SQLAlchemy ORM model) instance to a Pydantic UserResponse model.
    """
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        interest_keys=user.interest_keys,
        interest_text=user.interest_text,
        suggested_event_ids=user.suggested_event_ids,
        theme_preference=user.theme_preference or DEFAULT_THEME,
        language_preference=user.language_preference or DEFAULT_PREFERENCE_LANGUAGE,
    )


# ----- Authentication dependencies -----
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserORM:
    """Get the current authenticated user from the JWT token."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    user_id = decode_access_token(token)
    
    # If token is invalid or expired, user_id will be None
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.user_id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        # Detach the user from the session to use it outside
        db.expunge(user)
        return user