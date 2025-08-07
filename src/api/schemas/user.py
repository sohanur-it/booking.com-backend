from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

# User Registration
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

# User Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Password Reset
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

# User Response
class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    is_active: bool
    is_verified: bool
    genius_level: int
    total_bookings: int
    total_spent: float
    genius_discount_percentage: float
    preferred_currency: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# User Update
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    preferred_currency: Optional[str] = None
    marketing_emails: Optional[bool] = None

# Genius Loyalty Info
class GeniusInfo(BaseModel):
    level: int
    total_bookings: int
    total_spent: float
    discount_percentage: float
    next_level_bookings: int
    next_level_spent: float
    
    class Config:
        from_attributes = True

# Token Response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse 