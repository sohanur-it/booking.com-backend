from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import secrets
import string

from .database import get_db
from .models.user import User

# Security configuration
SECRET_KEY = "your-secret-key-here-change-in-production"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()

class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request):
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            return None
        return await super().__call__(request)

optional_security = OptionalHTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = verify_token(credentials.credentials)
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if credentials is None:
        return None
    try:
        return get_current_active_user(current_user=get_current_user(credentials, db))
    except HTTPException:
        return None

def generate_booking_reference() -> str:
    """Generate a unique booking reference."""
    # Format: BK-YYYYMMDD-XXXXX (e.g., BK-20241201-ABC12)
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    return f"BK-{date_part}-{random_part}"

def generate_reset_token() -> str:
    """Generate a password reset token."""
    return secrets.token_urlsafe(32)

def calculate_genius_level(total_bookings: int, total_spent: float) -> tuple[int, float]:
    """Calculate Genius level and discount percentage based on bookings and spending."""
    if total_bookings >= 15 and total_spent >= 5000:
        return 3, 20.0  # Level 3: 20% discount
    elif total_bookings >= 5 and total_spent >= 1000:
        return 2, 15.0  # Level 2: 15% discount
    elif total_bookings >= 1:
        return 1, 10.0  # Level 1: 10% discount
    else:
        return 0, 0.0   # No level: 0% discount 