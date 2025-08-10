from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class CarVendor(Base):
    __tablename__ = "car_vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(32), unique=True, index=True)


class CarLocation(Base):
    __tablename__ = "car_locations"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    airport_code = Column(String(8))
    address = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("car_vendors.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("car_locations.id"), nullable=False)

    make = Column(String(64), nullable=False)
    model = Column(String(64), nullable=False)
    car_class = Column(String(64), nullable=False)  # economy, compact, suv, premium
    seats = Column(Integer, default=4)
    doors = Column(Integer, default=4)
    transmission = Column(String(16), default="automatic")
    air_conditioning = Column(Boolean, default=True)

    base_price_per_day = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    available_quantity = Column(Integer, default=1)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    vendor = relationship("CarVendor")
    location = relationship("CarLocation")


class CarBookingStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class CarBooking(Base):
    __tablename__ = "car_bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    pickup_datetime = Column(DateTime, nullable=False)
    dropoff_datetime = Column(DateTime, nullable=False)
    pickup_location_id = Column(Integer, ForeignKey("car_locations.id"), nullable=False)
    dropoff_location_id = Column(Integer, ForeignKey("car_locations.id"), nullable=False)
    status = Column(String(16), default=CarBookingStatus.PENDING)

    total_price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    car = relationship("Car")
    pickup_location = relationship("CarLocation", foreign_keys=[pickup_location_id])
    dropoff_location = relationship("CarLocation", foreign_keys=[dropoff_location_id])


