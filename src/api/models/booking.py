from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(50), unique=True, index=True, nullable=False)
    
    # User and room relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    
    # Booking details
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    num_guests = Column(Integer, default=1)
    num_rooms = Column(Integer, default=1)
    
    # Guest information
    guest_names = Column(JSON)  # JSON array of guest names
    special_requests = Column(Text)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    genius_discount = Column(Float, default=0.0)
    taxes = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Cancellation policy
    free_cancellation = Column(Boolean, default=False)
    cancellation_deadline = Column(DateTime)
    cancellation_fee = Column(Float, default=0.0)
    
    # Status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Payment information
    payment_method = Column(String(50))  # credit_card, etc.
    payment_details = Column(JSON)  # Encrypted payment info
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    confirmed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    room = relationship("Room", back_populates="bookings")
    
    def __repr__(self):
        return f"<Booking(id={self.id}, reference='{self.booking_reference}', status='{self.status}')>"

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Payment method details
    method_type = Column(String(50), nullable=False)  # credit_card, debit_card
    card_type = Column(String(50))  # visa, mastercard, amex
    last_four_digits = Column(String(4))
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)
    cardholder_name = Column(String(255))
    
    # Security
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, type='{self.method_type}', last4='{self.last_four_digits}')>" 