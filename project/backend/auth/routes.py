"""
Authentication API routes.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Depends

from data.database.database_events import SessionLocal, UserORM  # pylint: disable=import-error
from services.email_service import send_password_reset_email  # pylint: disable=import-error

from .models import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
    PasswordResetRequest,
    PasswordReset,
)
from .utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    user_orm_to_response,
    get_current_user,
)


# Create router with prefix
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

# Thread pool for running blocking operations (email sending)
email_executor = ThreadPoolExecutor(max_workers=2)


@auth_router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user."""
    with SessionLocal() as db:
        # Check if email already exists
        existing_user = db.query(UserORM).filter(UserORM.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        new_user = UserORM(
            email=user_data.email,
            password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create access token
        access_token = create_access_token(new_user.user_id)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_orm_to_response(new_user)
        )


@auth_router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login a user."""
    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.email == user_data.email).first()
        
        if user is None or not verify_password(user_data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token = create_access_token(user.user_id)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_orm_to_response(user)
        )


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserORM = Depends(get_current_user)):
    """Get the current authenticated user's information."""
    return user_orm_to_response(current_user)


@auth_router.put("/me", response_model=UserResponse)
async def update_me(user_update: UserUpdate, current_user: UserORM = Depends(get_current_user)):
    """Update the current authenticated user's information."""
    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.user_id == current_user.user_id).first()
        
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if email is being changed and if it's already taken
        if user_update.email and user_update.email != user.email:
            existing_user = db.query(UserORM).filter(UserORM.email == user_update.email).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already in use")
            user.email = user_update.email
        
        # Update other fields
        if user_update.first_name:
            user.first_name = user_update.first_name
        if user_update.last_name:
            user.last_name = user_update.last_name
        if user_update.password:
            user.password = hash_password(user_update.password)
        if user_update.interest_keys is not None:
            user.interest_keys = user_update.interest_keys
        if user_update.interest_text is not None:
            user.interest_text = user_update.interest_text
        
        db.commit()
        db.refresh(user)
        
        return user_orm_to_response(user)


@auth_router.delete("/me")
async def delete_me(current_user: UserORM = Depends(get_current_user)):
    """Delete the current authenticated user's account."""
    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.user_id == current_user.user_id).first()
        
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        
        return {"message": "Account deleted successfully"}


@auth_router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """
    Request a password reset. Sends an email with the reset link.
    """
    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.email == request.email).first()
        
        # Always return success to prevent email enumeration attacks
        if user is None:
            return {"message": "If an account with that email exists, a password reset link has been sent."}
        
        # Create reset token
        reset_token = create_password_reset_token(request.email)
        
        # Send password reset email in a thread pool to not block the async loop
        loop = asyncio.get_event_loop()
        email_sent = await loop.run_in_executor(
            email_executor, 
            send_password_reset_email, 
            request.email, 
            reset_token
        )
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send password reset email. Please try again later.")
        
        return {"message": "If an account with that email exists, a password reset link has been sent."}


@auth_router.post("/reset-password")
async def reset_password(request: PasswordReset):
    """Reset password using the reset token."""
    email = decode_password_reset_token(request.token)
    
    if email is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    with SessionLocal() as db:
        user = db.query(UserORM).filter(UserORM.email == email).first()
        
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password
        user.password = hash_password(request.new_password)
        db.commit()
        
        return {"message": "Password reset successfully"}
