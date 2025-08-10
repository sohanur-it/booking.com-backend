from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Dict

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse, PasswordResetRequest, PasswordReset, UserUpdate, GeniusInfo
from ..auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    calculate_genius_level,
    get_current_user,
    ALGORITHM,
    SECRET_KEY
)
from jose import jwt, JWTError
# from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        date_of_birth=user_data.date_of_birth
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(db_user)
    )

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token."""
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )
@router.post("/password-reset-request")
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset (send reset token via email)."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}

    # Create reset token (short expiry)
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    reset_token = create_access_token(
        data={"sub": user.email, "action": "password_reset"},
        expires_delta=expires
    )

    # TODO: Send token via email with link like:
    # reset_url = f"https://yourfrontend.com/reset-password?token={reset_token}"
    # send_email(user.email, reset_url)

    return {
        "message": "If the email exists, a password reset link has been sent",
        "reset_token": reset_token  # Only for testing — remove in production
    }

@router.post("/password-reset")
def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """Reset password using token."""
    try:
        payload = jwt.decode(reset_data.token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("action") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid reset token")

        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.password_hash = get_password_hash(reset_data.new_password)
    db.commit()

    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information."""
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)

@router.get("/genius-info", response_model=GeniusInfo)
def get_genius_info(current_user: User = Depends(get_current_active_user)):
    """Get Genius loyalty program information."""
    level, discount = calculate_genius_level(current_user.total_bookings, current_user.total_spent)
    
    # Calculate next level requirements
    if level == 0:
        next_bookings = 1
        next_spent = 0
    elif level == 1:
        next_bookings = 5 - current_user.total_bookings
        next_spent = 1000 - current_user.total_spent
    elif level == 2:
        next_bookings = 15 - current_user.total_bookings
        next_spent = 5000 - current_user.total_spent
    else:
        next_bookings = 0
        next_spent = 0
    
    return GeniusInfo(
        level=level,
        total_bookings=current_user.total_bookings,
        total_spent=current_user.total_spent,
        discount_percentage=discount,
        next_level_bookings=max(0, next_bookings),
        next_level_spent=max(0, next_spent)
    )

@router.post("/logout")
def logout():
    """Logout user (client should discard token)."""
    return {"message": "Successfully logged out"} 