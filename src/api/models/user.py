from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from datetime import datetime
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Genius loyalty program fields
    genius_level = Column(Integer, default=1)  # 1, 2, 3 levels
    total_bookings = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    genius_discount_percentage = Column(Float, default=0.0)  # 10%, 15%, 20%
    
    # Preferences
    preferred_currency = Column(String(3), default="USD")
    preferred_language = Column(String(5), default="en")
    marketing_emails = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', genius_level={self.genius_level})>" 