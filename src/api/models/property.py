from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Property details
    property_type = Column(String(50))  # hotel, resort, apartment, etc.
    star_rating = Column(Integer)  # 1-5 stars
    total_rooms = Column(Integer)
    
    # Contact info
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    
    # Amenities and features
    amenities = Column(JSON)  # JSON array of amenity codes
    facilities = Column(JSON)  # JSON array of facility codes
    
    # Pricing and availability
    base_price = Column(Float)
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True)
    
    # Policies (for filtering)
    supports_free_cancellation = Column(Boolean, default=True)
    supports_no_prepayment = Column(Boolean, default=False)
    
    # Location details
    neighbourhood = Column(String(100))
    
    # Images
    images = Column(JSON)  # JSON array of image URLs
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    rooms = relationship("Room", back_populates="property")
    reviews = relationship("Review", back_populates="property")
    
    def __repr__(self):
        return f"<Property(id={self.id}, name='{self.name}', city='{self.city}')>"

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    room_type = Column(String(100))  # single, double, suite, etc.
    max_guests = Column(Integer, default=2)
    size_sqm = Column(Float)
    
    # Amenities
    room_amenities = Column(JSON)  # JSON array of room-specific amenities
    
    # Pricing
    base_price = Column(Float, nullable=False)
    genius_price = Column(Float)  # Discounted price for Genius members
    
    # Availability
    total_quantity = Column(Integer, default=1)
    available_quantity = Column(Integer, default=1)
    
    # Images
    images = Column(JSON)  # JSON array of image URLs
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room")
    rates = relationship("RoomRate", back_populates="room", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Room(id={self.id}, name='{self.name}', property_id={self.property_id})>" 

class RoomRate(Base):
    __tablename__ = "room_rates"
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    name = Column(String(100))  # e.g., "Non-refundable", "Breakfast included"
    description = Column(Text)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    includes_breakfast = Column(Boolean, default=False)
    includes_parking = Column(Boolean, default=False)
    free_cancellation = Column(Boolean, default=False)
    refundable_until = Column(DateTime, nullable=True)
    pay_at_property = Column(Boolean, default=False)
    # Relationships
    room = relationship("Room", back_populates="rates") 