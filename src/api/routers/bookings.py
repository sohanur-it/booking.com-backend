from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ..database import get_db
from ..models.booking import Booking, BookingStatus, PaymentStatus, PaymentMethod
from ..models.property import Room, Property, RoomRate
from ..models.user import User
from ..schemas.booking import (
    BookingCreate, BookingUpdate, BookingResponse, BookingWithRoom,
    BookingCancellation, PaymentMethodCreate, PaymentMethodResponse,
    BookingConfirmation, PriceCalculationRequest, PriceCalculationResponse,
    CartItem, CartQuoteRequest, CartItemQuote, CartQuoteResponse,
    BulkBookingRequest, BulkBookingResponse,
)
from ..auth import get_current_active_user, generate_booking_reference, calculate_genius_level

router = APIRouter(prefix="/bookings", tags=["Bookings"])

# Default application timezone (US)
DEFAULT_TZ = ZoneInfo("America/New_York")
HOLD_MINUTES = 15  # pending bookings hold window

# Payment methods endpoints (moved to top after router definition)
@router.post("/payment-methods", response_model=PaymentMethodResponse)
def create_payment_method(
    payment_data: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a new payment method."""
    if payment_data.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id
        ).update({"is_default": False})
    db_payment_method = PaymentMethod(
        user_id=current_user.id,
        **payment_data.dict()
    )
    db.add(db_payment_method)
    db.commit()
    db.refresh(db_payment_method)
    return PaymentMethodResponse.from_orm(db_payment_method)

@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
def get_payment_methods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all payment methods for the current user."""
    payment_methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.is_active == True
    ).all()
    return [PaymentMethodResponse.from_orm(pm) for pm in payment_methods]

@router.delete("/payment-methods/{payment_method_id}")
def delete_payment_method(
    payment_method_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a payment method."""
    payment_method = db.query(PaymentMethod).filter(
        and_(
            PaymentMethod.id == payment_method_id,
            PaymentMethod.user_id == current_user.id
        )
    ).first()
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    payment_method.is_active = False
    db.commit()
    return {"message": "Payment method deleted successfully"}

@router.post("/calculate-price", response_model=PriceCalculationResponse)
def calculate_price(
    request: PriceCalculationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """Calculate booking price including Genius discounts."""
    
    # Get room
    room = db.query(Room).filter(Room.id == request.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Normalize and interpret dates in US timezone by default
    ci = request.check_in_date if request.check_in_date.tzinfo else request.check_in_date.replace(tzinfo=DEFAULT_TZ)
    co = request.check_out_date if request.check_out_date.tzinfo else request.check_out_date.replace(tzinfo=DEFAULT_TZ)
    # Calculate base price (use selected rate if provided)
    nights = (co - ci).days
    unit_price = room.base_price
    selected_rate: Optional[RoomRate] = None
    if request.room_rate_id is not None:
        selected_rate = db.query(RoomRate).filter(
            RoomRate.id == request.room_rate_id,
            RoomRate.room_id == request.room_id
        ).first()
        if not selected_rate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room_rate_id for the selected room")
        unit_price = selected_rate.price
    base_price = unit_price * nights * request.num_rooms
    
    # Calculate Genius discount
    genius_discount = 0.0
    genius_discount_percentage = 0.0
    
    if current_user:
        level, discount_percentage = calculate_genius_level(
            current_user.total_bookings, current_user.total_spent
        )
        if level > 0 and room.genius_price:
            genius_discount = (base_price - room.genius_price * nights * request.num_rooms)
            genius_discount_percentage = discount_percentage
        elif level > 0:
            genius_discount = base_price * (discount_percentage / 100)
            genius_discount_percentage = discount_percentage
    
    # Calculate taxes (simplified - 10% tax rate)
    subtotal = base_price - genius_discount
    taxes = subtotal * 0.10
    
    # Total price
    total_price = subtotal + taxes
    
    # Cancellation policy
    free_cancellation = True  # Simplified
    cancellation_deadline = request.check_in_date - timedelta(days=1)
    cancellation_fee = 0.0 if free_cancellation else base_price * 0.10
    
    return PriceCalculationResponse(
        base_price=base_price,
        genius_discount=genius_discount,
        genius_discount_percentage=genius_discount_percentage,
        taxes=taxes,
        total_price=total_price,
        currency=room.property.currency if room.property else "USD",
        free_cancellation=free_cancellation,
        cancellation_deadline=cancellation_deadline,
        cancellation_fee=cancellation_fee,
        breakdown={
            "base_price": base_price,
            "genius_discount": -genius_discount,
            "subtotal": subtotal,
            "taxes": taxes,
            "total": total_price
        }
    )

@router.post("/", response_model=BookingResponse)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new booking."""

    # Verify room exists
    room = db.query(Room).filter(Room.id == booking_data.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    # If a room_rate_id is supplied, ensure it belongs to this room
    if booking_data.room_rate_id is not None:
        rr_ok = db.query(RoomRate.id).filter(
            RoomRate.id == booking_data.room_rate_id,
            RoomRate.room_id == booking_data.room_id
        ).first()
        if not rr_ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room_rate_id for the selected room")

    # Normalize and interpret dates in US timezone by default
    ci = booking_data.check_in_date if booking_data.check_in_date.tzinfo else booking_data.check_in_date.replace(tzinfo=DEFAULT_TZ)
    co = booking_data.check_out_date if booking_data.check_out_date.tzinfo else booking_data.check_out_date.replace(tzinfo=DEFAULT_TZ)
    # Nights calculation (redundant due to validator but kept for safety)
    nights = (co - ci).days
    if nights <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Check-out date must be after check-in date")

    # Check room availability for the requested dates
    # Use UTC boundaries when checking overlap; count confirmed and recent pending holds
    existing_bookings = db.query(Booking).filter(
        and_(
            Booking.room_id == booking_data.room_id,
            or_(
                Booking.status == BookingStatus.CONFIRMED,
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.created_at >= datetime.now(DEFAULT_TZ).astimezone(ZoneInfo("UTC")).replace(tzinfo=None) - timedelta(minutes=HOLD_MINUTES),
                ),
            ),
            or_(
                and_(
                    Booking.check_in_date < co.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
                    Booking.check_out_date > ci.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                )
            )
        )
    ).count()

    remaining = max(0, room.available_quantity - existing_bookings)
    if remaining < booking_data.num_rooms:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room not available for selected dates")

    # Calculate price using selected room rate when provided
    price_request = PriceCalculationRequest(
        room_id=booking_data.room_id,
        room_rate_id=booking_data.room_rate_id,
        check_in_date=ci,
        check_out_date=co,
        num_guests=booking_data.num_guests,
        num_rooms=booking_data.num_rooms,
        user_id=current_user.id
    )
    price_calc = calculate_price(price_request, db, current_user)

    # Create booking reference (assumed function)
    booking_reference = generate_booking_reference()

    # Create booking entry
    db_booking = Booking(
        booking_reference=booking_reference,
        user_id=current_user.id,
        room_id=booking_data.room_id,
        check_in_date=booking_data.check_in_date,
        check_out_date=booking_data.check_out_date,
        num_guests=booking_data.num_guests,
        num_rooms=booking_data.num_rooms,
        guest_names=booking_data.guest_names,
        special_requests=booking_data.special_requests,
        base_price=price_calc.base_price,
        genius_discount=price_calc.genius_discount,
        taxes=price_calc.taxes,
        total_price=price_calc.total_price,
        currency=price_calc.currency,
        free_cancellation=price_calc.free_cancellation,
        cancellation_deadline=price_calc.cancellation_deadline,
        cancellation_fee=price_calc.cancellation_fee,
        status=BookingStatus.PENDING,
        payment_status=PaymentStatus.PENDING
    )

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return BookingResponse.model_validate(db_booking)

@router.get("/", response_model=List[BookingWithRoom])
def get_user_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all bookings for the current user."""
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    
    booking_responses = []
    for booking in bookings:
        # Get room and property info
        room = db.query(Room).filter(Room.id == booking.room_id).first()
        property = db.query(Property).filter(Property.id == room.property_id).first() if room else None
        
        booking_dict = BookingResponse.from_orm(booking).dict()
        booking_dict.update({
            "room_name": room.name if room else "",
            "property_name": property.name if property else "",
            "property_address": property.address if property else "",
            "property_city": property.city if property else "",
            "property_country": property.country if property else ""
        })
        
        booking_responses.append(BookingWithRoom(**booking_dict))
    
    return booking_responses

@router.get("/{booking_id}", response_model=BookingWithRoom)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific booking."""
    booking = db.query(Booking).filter(
        and_(Booking.id == booking_id, Booking.user_id == current_user.id)
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Get room and property info
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    property = db.query(Property).filter(Property.id == room.property_id).first() if room else None
    
    booking_dict = BookingResponse.from_orm(booking).dict()
    booking_dict.update({
        "room_name": room.name if room else "",
        "property_name": property.name if property else "",
        "property_address": property.address if property else "",
        "property_city": property.city if property else "",
        "property_country": property.country if property else ""
    })
    
    return BookingWithRoom(**booking_dict)

@router.put("/{booking_id}/confirm", response_model=BookingResponse)
def confirm_booking(
    booking_id: int,
    confirmation: BookingConfirmation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Confirm a booking with payment."""
    booking = db.query(Booking).filter(
        and_(Booking.id == booking_id, Booking.user_id == current_user.id)
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking cannot be confirmed"
        )
    
    # Process payment (simplified - in real app you'd integrate with payment gateway)
    booking.status = BookingStatus.CONFIRMED
    booking.payment_status = PaymentStatus.PAID
    booking.confirmed_at = datetime.utcnow()
    
    # Update user's booking count and spending for Genius program
    current_user.total_bookings += 1
    current_user.total_spent += booking.total_price
    
    # Recalculate Genius level
    level, discount = calculate_genius_level(current_user.total_bookings, current_user.total_spent)
    current_user.genius_level = level
    current_user.genius_discount_percentage = discount
    
    db.commit()
    db.refresh(booking)
    
    return BookingResponse.from_orm(booking)


@router.post("/quote", response_model=CartQuoteResponse)
def quote_cart(
    payload: CartQuoteRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user),
):
    items_quotes: list[CartItemQuote] = []
    unavailable: list[int] = []
    subtotal = 0.0
    taxes_total = 0.0
    currency = "USD"

    for item in payload.items:
        room = db.query(Room).filter(Room.id == item.room_id).first()
        if not room:
            unavailable.append(item.room_id)
            continue
        currency = room.property.currency if room.property else currency
        # If a room_rate_id is supplied, ensure it belongs to this room and override price unit
        selected_rate: Optional[RoomRate] = None
        if item.room_rate_id is not None:
            selected_rate = db.query(RoomRate).filter(
                RoomRate.id == item.room_rate_id,
                RoomRate.room_id == item.room_id
            ).first()
            if not selected_rate:
                unavailable.append(item.room_id)
                continue
        # Availability
        overlapping = db.query(Booking).filter(
            and_(
                Booking.room_id == item.room_id,
                or_(
                    Booking.status == BookingStatus.CONFIRMED,
                    and_(
                        Booking.status == BookingStatus.PENDING,
                        Booking.created_at >= datetime.now(DEFAULT_TZ).astimezone(ZoneInfo("UTC")).replace(tzinfo=None) - timedelta(minutes=HOLD_MINUTES),
                    ),
                ),
                Booking.check_in_date < payload.check_out_date,
                Booking.check_out_date > payload.check_in_date,
            )
        ).count()
        remaining = max(0, (room.available_quantity or 0) - overlapping)
        if remaining < item.num_rooms:
            unavailable.append(item.room_id)
            items_quotes.append(CartItemQuote(
                room_id=item.room_id,
                available=remaining,
                requested=item.num_rooms,
                base_price=0.0,
                genius_discount=0.0,
                taxes=0.0,
                total_price=0.0,
                currency=currency,
            ))
            continue

        # Normalize dates to default timezone for consistency
        ci = payload.check_in_date if payload.check_in_date.tzinfo else payload.check_in_date.replace(tzinfo=DEFAULT_TZ)
        co = payload.check_out_date if payload.check_out_date.tzinfo else payload.check_out_date.replace(tzinfo=DEFAULT_TZ)
        price_req = PriceCalculationRequest(
            room_id=item.room_id,
            room_rate_id=item.room_rate_id,
            check_in_date=ci,
            check_out_date=co,
            num_guests=item.num_guests,
            num_rooms=item.num_rooms,
        )
        price = calculate_price(price_req, db, current_user)
        items_quotes.append(CartItemQuote(
            room_id=item.room_id,
            available=remaining,
            requested=item.num_rooms,
            base_price=price.base_price,
            genius_discount=price.genius_discount,
            taxes=price.taxes,
            total_price=price.total_price,
            currency=price.currency,
        ))
        subtotal += price.base_price - price.genius_discount
        taxes_total += price.taxes

    total = subtotal + taxes_total
    return CartQuoteResponse(
        items=items_quotes,
        subtotal=subtotal,
        taxes=taxes_total,
        total=total,
        currency=currency,
        unavailable_items=unavailable,
    )


## Cart endpoints removed as per requirements (stateless multi-room flow)


@router.post("/bulk-book", response_model=BulkBookingResponse)
def bulk_book(
    payload: BulkBookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Quote via existing quote_cart
    quote = quote_cart(CartQuoteRequest(items=payload.items, check_in_date=payload.check_in_date, check_out_date=payload.check_out_date), db, current_user)
    if quote.unavailable_items:
        raise HTTPException(status_code=400, detail={"unavailable_items": quote.unavailable_items})

    created: list[int] = []
    for iq in quote.items:
        db_booking = Booking(
            booking_reference=generate_booking_reference(),
            user_id=current_user.id,
            room_id=iq.room_id,
            check_in_date=payload.check_in_date,
            check_out_date=payload.check_out_date,
            num_guests=next(i.num_guests for i in payload.items if i.room_id == iq.room_id),
            num_rooms=next(i.num_rooms for i in payload.items if i.room_id == iq.room_id),
            base_price=iq.base_price,
            genius_discount=iq.genius_discount,
            taxes=iq.taxes,
            total_price=iq.total_price,
            currency=iq.currency,
            free_cancellation=True,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
        )
        db.add(db_booking); db.commit(); db.refresh(db_booking)
        created.append(db_booking.id)

    return BulkBookingResponse(
        booking_ids=created,
        subtotal=quote.subtotal,
        taxes=quote.taxes,
        total=quote.total,
        currency=quote.currency,
    )

@router.put("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    cancellation: BookingCancellation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a booking."""
    booking = db.query(Booking).filter(
        and_(Booking.id == booking_id, Booking.user_id == current_user.id)
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking cannot be cancelled"
        )
    
    # Check cancellation deadline
    if booking.cancellation_deadline and datetime.utcnow() > booking.cancellation_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cancellation deadline has passed"
        )
    
    # Cancel booking
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.utcnow()
    
    # Process refund if payment was made
    if booking.payment_status == PaymentStatus.PAID:
        refund_amount = booking.total_price - booking.cancellation_fee
        booking.payment_status = PaymentStatus.REFUNDED
        
        # Update user's spending (subtract the refunded amount)
        current_user.total_spent -= refund_amount
        
        # Recalculate Genius level
        level, discount = calculate_genius_level(current_user.total_bookings, current_user.total_spent)
        current_user.genius_level = level
        current_user.genius_discount_percentage = discount
    
    db.commit()
    db.refresh(booking)
    
    return BookingResponse.from_orm(booking) 