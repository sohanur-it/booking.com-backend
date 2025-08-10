from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from math import radians, cos, sin, asin, sqrt

from ..database import get_db
from ..models.property import Property, Room, RoomRate
from ..models.booking import Booking, BookingStatus
from ..models.review import Review
from ..schemas.property import (
    PropertySearch, PropertyCreate, PropertyUpdate, PropertyResponse,
    RoomCreate, RoomUpdate, RoomResponse, PropertyWithRooms, PropertySearchResponse,
    RoomWithRates, RoomRateResponse
)
from ..auth import get_current_active_user, calculate_genius_level
from ..models.user import User

router = APIRouter(prefix="/properties", tags=["Properties"])

# Default application timezone (US)
DEFAULT_TZ = ZoneInfo("America/New_York")
HOLD_MINUTES = 15  # pending bookings hold window

# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.orm import Session
# from sqlalchemy import and_, or_, func, desc
# from typing import List, Optional
# from datetime import datetime, timedelta, time
# from zoneinfo import ZoneInfo
# from math import radians, cos, sin, asin, sqrt

# from ..database import get_db
# from ..models.property import Property, Room
# from ..models.booking import Booking, BookingStatus
# from ..models.review import Review
# from ..schemas.property import (
#     PropertySearch, PropertyCreate, PropertyUpdate, PropertyResponse,
#     RoomCreate, RoomUpdate, RoomResponse, PropertyWithRooms, PropertySearchResponse
# )
# from ..auth import get_current_active_user, calculate_genius_level
# from ..models.user import User

# router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("/search", response_model=PropertySearchResponse)
def search_properties(
    destination: Optional[str] = Query(None),
    check_in: Optional[datetime] = Query(None),
    check_out: Optional[datetime] = Query(None),
    guests: int = Query(1),
    requested_rooms: int = Query(1),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    star_rating: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    amenities: Optional[str] = Query(None),
    facilities: Optional[str] = Query(None),
    room_facilities: Optional[str] = Query(None),
    review_score_min: Optional[float] = Query(None),
    free_cancellation: Optional[bool] = Query(None),
    no_prepayment: Optional[bool] = Query(None),
    near_landmark: Optional[str] = Query(None),
    neighbourhood: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    max_distance_km: Optional[float] = Query(None),
    sort_by: str = Query("recommended"),
    sort_order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search for properties with filters and live room availability."""
    query = db.query(Property).filter(Property.is_active == True)

    # --- Property-level filters ---
    if destination:
        query = query.filter(
            or_(
                Property.city.ilike(f"%{destination}%"),
                Property.country.ilike(f"%{destination}%"),
                Property.name.ilike(f"%{destination}%")
            )
        )

    if min_price is not None:
        query = query.filter(Property.base_price >= min_price)
    if max_price is not None:
        query = query.filter(Property.base_price <= max_price)

    if star_rating:
        ratings = [int(r.strip()) for r in star_rating.split(",")]
        query = query.filter(Property.star_rating.in_(ratings))

    if property_type:
        types = [t.strip() for t in property_type.split(",")]
        query = query.filter(Property.property_type.in_(types))

    if amenities:
        for a in [a.strip() for a in amenities.split(",")]:
            query = query.filter(Property.amenities.contains(a))

    if facilities:
        for f in [f.strip() for f in facilities.split(",")]:
            query = query.filter(Property.facilities.contains(f))

    if room_facilities:
        for rf in [rf.strip() for rf in room_facilities.split(",")]:
            query = query.filter(Property.facilities.contains(rf))

    if free_cancellation is not None:
        query = query.filter(Property.supports_free_cancellation == free_cancellation)
    if no_prepayment is not None:
        query = query.filter(Property.supports_no_prepayment == no_prepayment)

    if neighbourhood:
        query = query.filter(Property.neighbourhood.ilike(f"%{neighbourhood}%"))

    if near_landmark:
        key = near_landmark.lower()
        if key in ("beach", "near the beach"):
            query = query.filter(or_(
                Property.facilities.contains("beach_front"),
                Property.description.ilike("%beach%")
            ))
        elif key in ("city centre", "city center"):
            query = query.filter(Property.description.ilike("%city center%"))

    # --- Sorting ---
    if sort_by == "price":
        query = query.order_by(Property.base_price.desc() if sort_order == "desc" else Property.base_price.asc())
    elif sort_by == "rating":
        query = query.order_by(Property.star_rating.desc() if sort_order == "desc" else Property.star_rating.asc())
    else:
        query = query.order_by(Property.star_rating.desc(), Property.base_price.asc())

    properties = query.all()

    # --- Distance filter ---
    def haversine_km(lat1, lon1, lat2, lon2):
        rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = rlat2 - rlat1
        dlon = rlon2 - rlon1
        a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
        return 6371.0 * 2 * asin(sqrt(a))

    distance_map = {}
    if lat is not None and lon is not None:
        filtered = []
        for p in properties:
            if p.latitude is None or p.longitude is None:
                continue
            d = haversine_km(lat, lon, p.latitude, p.longitude)
            distance_map[p.id] = d
            if max_distance_km is None or d <= max_distance_km:
                filtered.append(p)
        properties = filtered
        if sort_by == "distance":
            properties.sort(key=lambda p: distance_map.get(p.id, float("inf")), reverse=(sort_order == "desc"))

    # --- Availability check ---
    properties_with_rooms = []
    # Normalize date inputs: ensure at least one-night window
    if check_in and check_out and check_out <= check_in:
        check_out = check_in + timedelta(days=1)
    for prop in properties:
        rooms_with_remaining = []
        best_deal = None
        min_price = float("inf")
        rooms = db.query(Room).filter(Room.property_id == prop.id).all()

        for room in rooms:
            # Capacity check
            if guests > room.max_guests:
                continue

            min_remaining = None
            if check_in and check_out:
                # Interpret inputs in US timezone by default
                start_local = check_in if check_in.tzinfo else check_in.replace(tzinfo=DEFAULT_TZ)
                end_local = check_out if check_out.tzinfo else check_out.replace(tzinfo=DEFAULT_TZ)
                tz = DEFAULT_TZ

                def day_range(d0, d1):
                    cur = datetime.combine(d0.date(), time(0), tz)
                    while cur < d1:
                        yield cur
                        cur = cur + timedelta(days=1)

                for d_local in day_range(start_local, end_local):
                    day_start_utc = d_local.astimezone(ZoneInfo("UTC"))
                    day_end_utc = (d_local + timedelta(days=1)).astimezone(ZoneInfo("UTC"))
                    ds = day_start_utc.replace(tzinfo=None)
                    de = day_end_utc.replace(tzinfo=None)

                    # Count confirmed and only non-expired pending holds
                    now_us = datetime.now(DEFAULT_TZ)
                    now_utc = now_us.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                    hold_threshold = now_utc - timedelta(minutes=HOLD_MINUTES)
                    booked_rooms = db.query(func.coalesce(func.sum(Booking.num_rooms), 0)).filter(
                        and_(
                            Booking.room_id == room.id,
                            or_(
                                Booking.status == BookingStatus.CONFIRMED,
                                and_(
                                    Booking.status == BookingStatus.PENDING,
                                    Booking.created_at >= hold_threshold,
                                ),
                            ),
                            Booking.check_in_date < de,
                            Booking.check_out_date > ds,
                        )
                    ).scalar() or 0

                    print(f"Booked rooms: {booked_rooms} room id: {room.id} check_in: {check_in} check_out: {check_out}")
                    print(f"Available quantity: {room.available_quantity}")
                    print(f"Total quantity: {room.total_quantity}")

                    # Determine operational capacity: prefer available_quantity as a cap, fall back to total_quantity
                    capacity = (
                        room.available_quantity
                        if room.available_quantity is not None
                        else (room.total_quantity or 0)
                    )
                    available = max(0, capacity - int(booked_rooms))
                    if min_remaining is None or available < min_remaining:
                        min_remaining = available
                # Fallback if no days iterated (edge case)
                if min_remaining is None:
                    ds = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                    de = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                    now_us = datetime.now(DEFAULT_TZ)
                    now_utc = now_us.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                    hold_threshold = now_utc - timedelta(minutes=HOLD_MINUTES)
                    booked_rooms = db.query(func.coalesce(func.sum(Booking.num_rooms), 0)).filter(
                        and_(
                            Booking.room_id == room.id,
                            or_(
                                Booking.status == BookingStatus.CONFIRMED,
                                and_(
                                    Booking.status == BookingStatus.PENDING,
                                    Booking.created_at >= hold_threshold,
                                ),
                            ),
                            Booking.check_in_date < de,
                            Booking.check_out_date > ds,
                        )
                    ).scalar() or 0
                    capacity = (
                        room.available_quantity
                        if room.available_quantity is not None
                        else (room.total_quantity or 0)
                    )
                    min_remaining = max(0, capacity - int(booked_rooms))

            remaining = min_remaining
            # If dates are provided and the room cannot satisfy the requested number of rooms, skip it
            if check_in and check_out and remaining is not None and remaining < requested_rooms:
                continue
            # If no dates are provided, do not show remaining count
            if not (check_in and check_out):
                remaining = None

            room_dict = RoomResponse.model_validate(room, from_attributes=True).model_dump()
            room_dict.pop("available_quantity", None)
            room_dict.pop("total_quantity", None)
            room_dict["remaining"] = remaining
            # Attach room rates in search response as well
            rates = db.query(RoomRate).filter(RoomRate.room_id == room.id).all()
            room_dict["room_rates"] = [
                {
                    "id": rr.id,
                    "name": rr.name,
                    "description": rr.description,
                    "price": rr.price,
                    "currency": rr.currency or (prop.currency or "USD"),
                    "includes_breakfast": bool(rr.includes_breakfast),
                    "includes_parking": bool(rr.includes_parking),
                    "free_cancellation": bool(rr.free_cancellation),
                    "refundable_until": rr.refundable_until.isoformat() if rr.refundable_until else None,
                    "pay_at_property": bool(rr.pay_at_property),
                }
                for rr in rates
            ]
            rooms_with_remaining.append(room_dict)

            if room.base_price < min_price and (remaining is None or remaining > 0):
                min_price = room.base_price
                best_deal = (room, remaining)

        if rooms_with_remaining:
            property_dict = PropertyResponse.model_validate(prop, from_attributes=True).model_dump()
            property_dict["rooms"] = rooms_with_remaining

            if best_deal:
                room, remaining = best_deal
                deal_block = {
                    "type": "Limited-time Deal",
                    "room_type": room.room_type,
                    "room_features": room.room_amenities or [],
                    "nights": (check_out - check_in).days if check_in and check_out else 1,
                    "guests": guests,
                    "price": {
                        "original": room.base_price,
                        "currency": prop.currency or "USD",
                        "discounted": room.base_price,
                    }
                }
                if check_in and check_out and remaining is not None:
                    deal_block["availability_note"] = f"Only {remaining} left at this price on our site" if remaining <= 5 else "Available"
                    deal_block["remaining"] = remaining
                property_dict["deal"] = deal_block

            properties_with_rooms.append(PropertyWithRooms(**property_dict))

    # --- Pagination ---
    total_count = len(properties_with_rooms)
    total_pages = (total_count + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paged_properties = properties_with_rooms[start:end]

    return PropertySearchResponse(
        properties=paged_properties,
        total_count=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages
    )




@router.get("/{property_id}/details")
def get_property_details(
    property_id: int,
    check_in: Optional[datetime] = Query(None),
    check_out: Optional[datetime] = Query(None),
    adults: int = Query(2),
    children: int = Query(0),
    rooms: int = Query(1),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user),
):
    """Single, rich payload for property details page.
    Includes location, photos, review aggregates, amenities, availability, policies, reviews, and simple nearby hints.
    """
    prop = db.query(Property).filter(Property.id == property_id, Property.is_active == True).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    # Photos
    photos = []
    if prop.images:
        for url in prop.images:
            photos.append({"url": url, "alt": prop.name})

    # Ratings and distribution
    reviews_q = db.query(Review).filter(Review.property_id == property_id, Review.is_approved == True)
    total_reviews = reviews_q.count()
    avg_score = float(db.query(func.avg(Review.overall_rating)).filter(Review.property_id == property_id, Review.is_approved == True).scalar() or 0.0)
    breakdown = {
        "cleanliness": float(db.query(func.avg(Review.cleanliness_rating)).filter(Review.property_id == property_id, Review.is_approved == True).scalar() or 0.0),
        "comfort": float(db.query(func.avg(Review.comfort_rating)).filter(Review.property_id == property_id, Review.is_approved == True).scalar() or 0.0),
        "location": float(db.query(func.avg(Review.location_rating)).filter(Review.property_id == property_id, Review.is_approved == True).scalar() or 0.0),
        "facilities": float(db.query(func.avg(Review.facilities_rating)).filter(Review.property_id == property_id, Review.is_approved == True).scalar() or 0.0),
        "staff": float(db.query(func.avg(Review.staff_rating)).filter(Review.property_id == property_id, Review.is_approved == True).scalar() or 0.0),
        "value_for_money": float(db.query(func.avg(Review.value_for_money_rating)).filter(Review.property_id == property_id, Review.is_approved == True).scalar() or 0.0),
        "free_wifi": float(db.query(func.avg(Review.wifi_rating)).filter(Review.property_id == property_id, Review.is_approved == True).scalar() or 0.0),
    }
    review_count_by_score = {}
    for s in range(1, 11):
        review_count_by_score[str(s)] = reviews_q.filter(Review.overall_rating == s).count()
    review_count_by_score["5_or_below"] = sum(review_count_by_score[str(s)] for s in range(1, 6))

    # Amenities
    amenities = {
        "general": prop.amenities or [],
        "room": list({rf for rf in (prop.facilities or [])})  # reuse for demo
    }

    # Genius discount
    discount_pct = 0.0
    if current_user:
        level, pct = calculate_genius_level(current_user.total_bookings, current_user.total_spent)
        discount_pct = float(pct)

    # Availability and room pricing (now with per-day breakdown and remaining count, only if dates provided)
    avail = []
    prop_rooms = db.query(Room).filter(Room.property_id == property_id).all()
    # Default timezone for interpreting inputs
    tz = DEFAULT_TZ
    # Normalize date inputs: ensure at least one-night window
    if check_in and check_out and check_out <= check_in:
        check_out = check_in + timedelta(days=1)
    if check_in and check_out:
        start_local = check_in if check_in.tzinfo else check_in.replace(tzinfo=tz)
        end_local = check_out if check_out.tzinfo else check_out.replace(tzinfo=tz)
        def day_range(d0: datetime, d1: datetime):
            cur = d0
            cur = datetime.combine(cur.date(), time(0), tz)
            while cur < d1:
                yield cur
                cur = cur + timedelta(days=1)
    else:
        start_local = end_local = None
        def day_range(d0, d1):
            return []

    for room in prop_rooms:
        # capacity check (simple)
        if adults + children > room.max_guests:
            continue
        base = room.base_price
        final = base
        discount_block = None
        if discount_pct > 0:
            final = round(base * (1 - discount_pct / 100), 2)
            discount_block = {"type": "Genius", "percent": discount_pct, "final_price": final}
        daily = []
        available_dates = []
        min_remaining = None
        if check_in and check_out:
            for d_local in day_range(start_local, end_local):
                day_start_utc = d_local.astimezone(ZoneInfo("UTC"))
                day_end_utc = (d_local + timedelta(days=1)).astimezone(ZoneInfo("UTC"))
                ds = day_start_utc.replace(tzinfo=None)
                de = day_end_utc.replace(tzinfo=None)
                now_us = datetime.now(DEFAULT_TZ)
                now_utc = now_us.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                hold_threshold = now_utc - timedelta(minutes=HOLD_MINUTES)
                booked_rooms = db.query(func.coalesce(func.sum(Booking.num_rooms), 0)).filter(
                    and_(
                        Booking.room_id == room.id,
                        or_(
                            Booking.status == BookingStatus.CONFIRMED,
                            and_(
                                Booking.status == BookingStatus.PENDING,
                                Booking.created_at >= hold_threshold,
                            ),
                        ),
                        Booking.check_in_date < de,
                        Booking.check_out_date > ds,
                    )
                ).scalar() or 0
                capacity = (
                    room.available_quantity
                    if room.available_quantity is not None
                    else (room.total_quantity or 0)
                )
                available = max(0, capacity - int(booked_rooms))
                day_key = d_local.date().isoformat()
                daily.append({
                    "date": day_key,
                    "available": available,
                    "total": capacity,
                })
                if available > 0:
                    available_dates.append(day_key)
                if min_remaining is None or available < min_remaining:
                    min_remaining = available
            # Only show room if available for all days requested
            if any(d["available"] < rooms for d in daily):
                continue
        else:
            # No date range: just show total available
            available = room.available_quantity or 0
            min_remaining = None  # Do not show remaining if no dates
            daily = []
            available_dates = []
        room_block = {
            "room_id": room.id,
            "room_name": room.name,
            "photos": [{"url": u, "alt": room.name} for u in (room.images or [])],
            "capacity": {"adults": min(room.max_guests, adults), "children": max(0, children)},
            "size_sqm": room.size_sqm,
            "bed_type": room.room_type,
            "price": {
                "base": base,
                "currency": prop.currency or "USD",
                "discount": discount_block,
            },
            "cancellation_policy": "Free cancellation until 1 day before arrival" if prop.supports_free_cancellation else "Non-refundable",
            "booking_conditions": [
                "No prepayment needed" if prop.supports_no_prepayment else "Prepayment may be required",
                "Pay at the property" if prop.supports_no_prepayment else "Pay online",
            ],
            "available_dates": available_dates,
            "daily": daily,
        }
        if check_in and check_out:
            room_block["remaining"] = min_remaining
        # Include room rates nested under each room in details view
        rates = db.query(RoomRate).filter(RoomRate.room_id == room.id).all()
        room_block["room_rates"] = [
            {
                "id": rr.id,
                "name": rr.name,
                "description": rr.description,
                "price": rr.price,
                "currency": rr.currency or (prop.currency or "USD"),
                "includes_breakfast": bool(rr.includes_breakfast),
                "includes_parking": bool(rr.includes_parking),
                "free_cancellation": bool(rr.free_cancellation),
                "refundable_until": rr.refundable_until.isoformat() if rr.refundable_until else None,
                "pay_at_property": bool(rr.pay_at_property),
            }
            for rr in rates
        ]
        # Do not include static fields
        # room_block["available_quantity"] = ...
        # room_block["total_quantity"] = ...
        avail.append(room_block)

    # Reviews – latest few
    latest_reviews = []
    latest_q = reviews_q.order_by(desc(Review.created_at)).limit(5).all()
    for r in latest_q:
        user = db.query(User).filter(User.id == r.user_id).first()
        latest_reviews.append({
            "id": r.id,
            "user": {"name": f"{user.first_name}" if user else "", "country": ""},
            "rating": r.overall_rating,
            "title": r.title,
            "comment": r.content,
            "date": r.created_at.date().isoformat() if r.created_at else None,
            "helpful_votes": r.helpful_votes,
        })

    # Nearby places (heuristic demo)
    nearby = []
    if prop.facilities and "beach_front" in prop.facilities:
        nearby.append({"type": "Beach", "name": "Nearest Beach", "distance_meters": 300})

    payload = {
        "id": prop.id,
        "name": prop.name,
        "location": {
            "address": prop.address,
            "city": prop.city,
            "country": prop.country,
            "latitude": prop.latitude,
            "longitude": prop.longitude,
            "map_url": None,
        },
        "photos": photos,
        "rating": {
            "average_score": avg_score,
            "total_reviews": total_reviews,
            "breakdown": breakdown,
            "review_count_by_score": review_count_by_score,
        },
        "amenities": amenities,
        "availability": avail,
        "policies": {
            "check_in": "14:00",
            "check_out": "12:00",
            "children": "Children of all ages are welcome",
            "pets": "Pets are not allowed",
            "payment_methods": ["Credit card", "Debit card", "Cash"],
        },
        "reviews": {
            "latest": latest_reviews,
            "summary": {
                "most_common_positive": "Excellent location" if avg_score >= 8 else "",
                "most_common_negative": "Breakfast variety could improve" if avg_score < 9 else "",
            },
        },
        "nearby_places": nearby,
    }

    return payload


@router.post("/", response_model=PropertyResponse)
def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new property (admin only)."""
    # In a real app, you'd check if user is admin
    # For demo purposes, we'll allow any authenticated user
    
    db_property = Property(**property_data.dict())
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return PropertyResponse.model_validate(db_property, from_attributes=True)
    
    # return PropertyResponse.from_orm(db_property)

@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a property (admin only)."""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Update fields
    for field, value in property_data.dict(exclude_unset=True).items():
        setattr(property, field, value)
    
    db.commit()
    db.refresh(property)
    return PropertyResponse.model_validate(property, from_attributes=True)
    
    # return PropertyResponse.from_orm(property)

@router.delete("/{property_id}")
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a property (admin only)."""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Soft delete
    property.is_active = False
    db.commit()
    
    return {"message": "Property deleted successfully"}

# Room endpoints
@router.post("/{property_id}/rooms", response_model=RoomResponse)
def create_room(
    property_id: int,
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new room for a property."""
    # Verify property exists
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    room_data_dict = room_data.dict()
    room_data_dict["property_id"] = property_id
    
    db_room = Room(**room_data_dict)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return RoomResponse.model_validate(db_room, from_attributes=True)
    
    # return RoomResponse.from_orm(db_room)

@router.put("/rooms/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a room."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Update fields
    for field, value in room_data.dict(exclude_unset=True).items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    return RoomResponse.model_validate(room, from_attributes= True)
    
    # return RoomResponse.from_orm(room)

@router.get("/rooms/{room_id}", response_model=RoomWithRates)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Get a specific room."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    # Attach room rates
    rates = db.query(RoomRate).filter(RoomRate.room_id == room.id).all()
    room_payload = RoomWithRates.model_validate(room, from_attributes=True).model_dump()
    room_payload["room_rates"] = [RoomRateResponse.model_validate(rr, from_attributes=True).model_dump() for rr in rates]
    return RoomWithRates(**room_payload)
    # return RoomResponse.from_orm(room)

@router.delete("/rooms/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a room."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    db.delete(room)
    db.commit()
    
    return {"message": "Room deleted successfully"} 