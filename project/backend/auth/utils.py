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
from .models import UserResponse


# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
PASSWORD_RESET_EXPIRE_HOURS = 1

# Security
security = HTTPBearer(auto_error=False)


# ----- Password hashing utilities -----
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ----- JWT utilities -----
def create_access_token(user_id: int) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """Decode a JWT access token and return the user_id."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create a JWT token for password reset."""
    expire = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
    payload = {
        "sub": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "password_reset"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_password_reset_token(token: str) -> Optional[str]:
    """Decode a password reset token and return the email."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
    )


# ----- Authentication dependencies -----
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserORM:
    """Get the current authenticated user from the JWT token."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    user_id = decode_access_token(token)
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.user_id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        # Detach the user from the session to use it outside
        db.expunge(user)
        return user


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[UserORM]:
    """Get the current user if authenticated, otherwise return None."""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
