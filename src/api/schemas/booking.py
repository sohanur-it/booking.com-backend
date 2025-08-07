from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

# Booking Create
class BookingCreate(BaseModel):
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    num_guests: int = 1
    num_rooms: int = 1
    guest_names: Optional[List[str]] = None
    special_requests: Optional[str] = None
    payment_method_id: Optional[int] = None
    
    @validator('check_out_date')
    def validate_checkout_date(cls, v, values):
        if 'check_in_date' in values and v <= values['check_in_date']:
            raise ValueError('Check-out date must be after check-in date')
        return v
    
    @validator('num_guests')
    def validate_guests(cls, v):
        if v < 1:
            raise ValueError('Number of guests must be at least 1')
        return v

# Booking Update
class BookingUpdate(BaseModel):
    guest_names: Optional[List[str]] = None
    special_requests: Optional[str] = None
    num_guests: Optional[int] = None
    
    @validator('num_guests')
    def validate_guests(cls, v):
        if v is not None and v < 1:
            raise ValueError('Number of guests must be at least 1')
        return v

# Booking Response
class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    user_id: int
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    num_guests: int
    num_rooms: int
    guest_names: Optional[List[str]]
    special_requests: Optional[str]
    base_price: float
    genius_discount: float
    taxes: float
    total_price: float
    currency: str
    free_cancellation: bool
    cancellation_deadline: Optional[datetime]
    cancellation_fee: float
    status: BookingStatus
    payment_status: PaymentStatus
    payment_method: Optional[str]
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Booking with Room Details
class BookingWithRoom(BookingResponse):
    room_name: str
    property_name: str
    property_address: str
    property_city: str
    property_country: str

# Booking Cancellation
class BookingCancellation(BaseModel):
    reason: Optional[str] = None
    refund_amount: Optional[float] = None

# Payment Method Create
class PaymentMethodCreate(BaseModel):
    method_type: str  # credit_card, debit_card
    card_type: Optional[str] = None  # visa, mastercard, amex
    last_four_digits: str
    expiry_month: int
    expiry_year: int
    cardholder_name: str
    is_default: bool = False
    
    @validator('expiry_month')
    def validate_expiry_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('Expiry month must be between 1 and 12')
        return v
    
    @validator('expiry_year')
    def validate_expiry_year(cls, v):
        if v < datetime.now().year:
            raise ValueError('Expiry year cannot be in the past')
        return v
    
    @validator('last_four_digits')
    def validate_last_four_digits(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError('Last four digits must be exactly 4 digits')
        return v

# Payment Method Response
class PaymentMethodResponse(BaseModel):
    id: int
    user_id: int
    method_type: str
    card_type: Optional[str]
    last_four_digits: str
    expiry_month: int
    expiry_year: int
    cardholder_name: str
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Booking Confirmation
class BookingConfirmation(BaseModel):
    booking_id: int
    payment_method_id: Optional[int] = None
    payment_details: Optional[Dict[str, Any]] = None

# Price Calculation Request
class PriceCalculationRequest(BaseModel):
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    num_guests: int = 1
    num_rooms: int = 1
    user_id: Optional[int] = None  # For Genius discount calculation

# Price Calculation Response
class PriceCalculationResponse(BaseModel):
    base_price: float
    genius_discount: float
    genius_discount_percentage: float
    taxes: float
    total_price: float
    currency: str
    free_cancellation: bool
    cancellation_deadline: Optional[datetime]
    cancellation_fee: float
    breakdown: Dict[str, float]  # Detailed price breakdown 