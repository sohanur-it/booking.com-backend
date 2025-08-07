from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Property Search
class PropertySearch(BaseModel):
    destination: Optional[str] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    guests: Optional[int] = 1
    rooms: Optional[int] = 1
    adults: Optional[int] = 1
    children: Optional[int] = 0
    infants: Optional[int] = 0
    
    # Filters
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    star_rating: Optional[List[int]] = None
    property_type: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    facilities: Optional[List[str]] = None
    
    # Sorting
    sort_by: Optional[str] = "recommended"  # price, rating, distance, etc.
    sort_order: Optional[str] = "asc"  # asc, desc
    
    # Pagination
    page: Optional[int] = 1
    limit: Optional[int] = 20

# Property Create/Update
class PropertyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    city: str
    country: str
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = None
    star_rating: Optional[int] = None
    total_rooms: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    amenities: Optional[List[str]] = None
    facilities: Optional[List[str]] = None
    base_price: Optional[float] = None
    currency: str = "USD"
    images: Optional[List[str]] = None

class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = None
    star_rating: Optional[int] = None
    total_rooms: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    amenities: Optional[List[str]] = None
    facilities: Optional[List[str]] = None
    base_price: Optional[float] = None
    currency: Optional[str] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None

# Property Response
class PropertyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    address: str
    city: str
    country: str
    postal_code: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    property_type: Optional[str]
    star_rating: Optional[int]
    total_rooms: Optional[int]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    amenities: Optional[List[str]]
    facilities: Optional[List[str]]
    base_price: Optional[float]
    currency: str
    is_active: bool
    images: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Room Create/Update
class RoomCreate(BaseModel):
    property_id: int
    name: str
    description: Optional[str] = None
    room_type: Optional[str] = None
    max_guests: int = 2
    size_sqm: Optional[float] = None
    room_amenities: Optional[List[str]] = None
    base_price: float
    genius_price: Optional[float] = None
    total_quantity: int = 1
    available_quantity: int = 1
    images: Optional[List[str]] = None

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    room_type: Optional[str] = None
    max_guests: Optional[int] = None
    size_sqm: Optional[float] = None
    room_amenities: Optional[List[str]] = None
    base_price: Optional[float] = None
    genius_price: Optional[float] = None
    total_quantity: Optional[int] = None
    available_quantity: Optional[int] = None
    images: Optional[List[str]] = None

# Room Response
class RoomResponse(BaseModel):
    id: int
    property_id: int
    name: str
    description: Optional[str]
    room_type: Optional[str]
    max_guests: int
    size_sqm: Optional[float]
    room_amenities: Optional[List[str]]
    base_price: float
    genius_price: Optional[float]
    total_quantity: int
    available_quantity: int
    images: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Property with Rooms
class PropertyWithRooms(PropertyResponse):
    rooms: List[RoomResponse] = []

# Search Response
class PropertySearchResponse(BaseModel):
    properties: List[PropertyWithRooms]
    total_count: int
    page: int
    limit: int
    total_pages: int 