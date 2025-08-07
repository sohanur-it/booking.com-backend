from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models.property import Property, Room
from ..models.booking import Booking, BookingStatus
from ..schemas.property import (
    PropertySearch, PropertyCreate, PropertyUpdate, PropertyResponse,
    RoomCreate, RoomUpdate, RoomResponse, PropertyWithRooms, PropertySearchResponse
)
from ..auth import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/properties", tags=["Properties"])

@router.get("/search", response_model=PropertySearchResponse)
def search_properties(
    destination: Optional[str] = Query(None, description="Search destination"),
    check_in: Optional[datetime] = Query(None, description="Check-in date"),
    check_out: Optional[datetime] = Query(None, description="Check-out date"),
    guests: int = Query(1, description="Number of guests"),
    rooms: int = Query(1, description="Number of rooms"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    star_rating: Optional[str] = Query(None, description="Star ratings (comma-separated)"),
    property_type: Optional[str] = Query(None, description="Property types (comma-separated)"),
    amenities: Optional[str] = Query(None, description="Amenities (comma-separated)"),
    sort_by: str = Query("recommended", description="Sort by: price, rating, distance"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Search for properties with filters and availability."""
    
    # Build base query
    query = db.query(Property).filter(Property.is_active == True)
    
    # Destination search
    if destination:
        query = query.filter(
            or_(
                Property.city.ilike(f"%{destination}%"),
                Property.country.ilike(f"%{destination}%"),
                Property.name.ilike(f"%{destination}%")
            )
        )
    
    # Price filters
    if min_price is not None:
        query = query.filter(Property.base_price >= min_price)
    if max_price is not None:
        query = query.filter(Property.base_price <= max_price)
    
    # Star rating filter
    if star_rating:
        ratings = [int(r.strip()) for r in star_rating.split(",")]
        query = query.filter(Property.star_rating.in_(ratings))
    
    # Property type filter
    if property_type:
        types = [t.strip() for t in property_type.split(",")]
        query = query.filter(Property.property_type.in_(types))
    
    # Amenities filter
    if amenities:
        amenity_list = [a.strip() for a in amenities.split(",")]
        # This is a simplified filter - in production you'd use JSON operators
        for amenity in amenity_list:
            query = query.filter(Property.amenities.contains(amenity))
    
    # Sorting
    if sort_by == "price":
        if sort_order == "desc":
            query = query.order_by(Property.base_price.desc())
        else:
            query = query.order_by(Property.base_price.asc())
    elif sort_by == "rating":
        if sort_order == "desc":
            query = query.order_by(Property.star_rating.desc())
        else:
            query = query.order_by(Property.star_rating.asc())
    else:  # recommended - by rating then price
        query = query.order_by(Property.star_rating.desc(), Property.base_price.asc())
    
    # Pagination
    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit
    offset = (page - 1) * limit
    
    properties = query.offset(offset).limit(limit).all()
    
    # Load rooms for each property
    properties_with_rooms = []
    for property in properties:
        rooms_query = db.query(Room).filter(
            and_(
                Room.property_id == property.id,
                Room.available_quantity > 0
            )
        )
        
        # Availability check if dates provided
        if check_in and check_out:
            # Get booked rooms for the date range
            booked_rooms = db.query(Booking.room_id).filter(
                and_(
                    Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                    or_(
                        and_(Booking.check_in_date < check_out, Booking.check_out_date > check_in)
                    )
                )
            ).subquery()
            
            rooms_query = rooms_query.filter(~Room.id.in_(booked_rooms))
        
        rooms = rooms_query.all()
        
        # Create property with rooms
        property_dict = PropertyResponse.from_orm(property).dict()
        property_dict["rooms"] = [RoomResponse.from_orm(room).dict() for room in rooms]
        properties_with_rooms.append(PropertyWithRooms(**property_dict))
    
    return PropertySearchResponse(
        properties=properties_with_rooms,
        total_count=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.get("/{property_id}", response_model=PropertyWithRooms)
def get_property(property_id: int, db: Session = Depends(get_db)):
    """Get a specific property with its rooms."""
    property = db.query(Property).filter(
        and_(Property.id == property_id, Property.is_active == True)
    ).first()
    
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Get rooms
    rooms = db.query(Room).filter(Room.property_id == property_id).all()
    
    # Create response
    property_dict = PropertyResponse.from_orm(property).dict()
    property_dict["rooms"] = [RoomResponse.from_orm(room).dict() for room in rooms]
    
    return PropertyWithRooms(**property_dict)

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
    
    return PropertyResponse.from_orm(db_property)

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
    
    return PropertyResponse.from_orm(property)

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
    
    return RoomResponse.from_orm(db_room)

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
    
    return RoomResponse.from_orm(room)

@router.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Get a specific room."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    return RoomResponse.from_orm(room)

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