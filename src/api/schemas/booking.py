from pydantic import BaseModel, field_validator, Field
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
    room_rate_id: Optional[int] = None
    check_in_date: datetime
    check_out_date: datetime
    num_guests: int = 1
    num_rooms: int = 1
    guest_names: Optional[List[str]] = None
    special_requests: Optional[str] = None
    payment_method_id: Optional[int] = None

    @field_validator('check_out_date')
    @classmethod
    def validate_checkout_date(cls, v, info):
        check_in = info.data.get('check_in_date')
        if check_in and v <= check_in:
            raise ValueError('Check-out date must be after check-in date')
        return v

    @field_validator('num_guests')
    @classmethod
    def validate_guests(cls, v):
        if v < 1:
            raise ValueError('Number of guests must be at least 1')
        return v


# Booking Update
class BookingUpdate(BaseModel):
    guest_names: Optional[List[str]] = None
    special_requests: Optional[str] = None
    num_guests: Optional[int] = None

    @field_validator('num_guests')
    @classmethod
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

    model_config = dict(from_attributes=True)


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

    @field_validator('expiry_month')
    @classmethod
    def validate_expiry_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('Expiry month must be between 1 and 12')
        return v

    @field_validator('expiry_year')
    @classmethod
    def validate_expiry_year(cls, v):
        from datetime import datetime as dt
        if v < dt.now().year:
            raise ValueError('Expiry year cannot be in the past')
        return v

    @field_validator('last_four_digits')
    @classmethod
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

    model_config = dict(from_attributes=True)


# Booking Confirmation
class BookingConfirmation(BaseModel):
    booking_id: int
    payment_method_id: Optional[int] = None
    payment_details: Optional[Dict[str, Any]] = None


# Price Calculation Request
class PriceCalculationRequest(BaseModel):
    room_id: int
    room_rate_id: Optional[int] = None
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


# Cart quoting for multiple rooms
class CartItem(BaseModel):
    room_id: int
    room_rate_id: Optional[int] = None
    num_rooms: int = 1
    num_guests: int = 1


class CartQuoteRequest(BaseModel):
    items: List[CartItem]
    check_in_date: datetime
    check_out_date: datetime


class CartItemQuote(BaseModel):
    room_id: int
    available: int
    requested: int
    base_price: float
    genius_discount: float
    taxes: float
    total_price: float
    currency: str


class CartQuoteResponse(BaseModel):
    items: List[CartItemQuote]
    subtotal: float
    taxes: float
    total: float
    currency: str
    unavailable_items: List[int] = []


# Persisted cart
class CartCreate(BaseModel):
    check_in_date: datetime
    check_out_date: datetime
    items: List[CartItem]


class CartItemResponse(BaseModel):
    id: int
    room_id: int
    num_rooms: int
    num_guests: int
    base_price: float
    genius_discount: float
    taxes: float
    total_price: float
    currency: str

    model_config = dict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    user_id: Optional[int]
    check_in_date: datetime
    check_out_date: datetime
    status: str
    currency: str
    items: List[CartItemResponse]
    subtotal: float
    taxes: float
    total: float

    model_config = dict(from_attributes=True)


# Bulk booking without cart persistence
class BulkBookingRequest(BaseModel):
    items: List[CartItem]
    check_in_date: datetime
    check_out_date: datetime


class BulkBookingResponse(BaseModel):
    booking_ids: List[int]
    subtotal: float
    taxes: float
    total: float
    currency: str
