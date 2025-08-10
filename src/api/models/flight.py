from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(8), unique=True, index=True, nullable=False)  # IATA or ICAO
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)

    def __repr__(self) -> str:  # pragma: no cover - representational
        return f"<Airport(code='{self.code}', city='{self.city}', country='{self.country}')>"


class Carrier(Base):
    __tablename__ = "carriers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(8), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - representational
        return f"<Carrier(code='{self.code}', name='{self.name}')>"


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=False)
    flight_number = Column(String(16), nullable=False)
    origin_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    destination_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    is_nonstop = Column(Boolean, default=True)

    base_price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    seats_economy = Column(Integer, default=0)
    seats_business = Column(Integer, default=0)
    seats_first = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    carrier = relationship("Carrier")
    origin = relationship("Airport", foreign_keys=[origin_airport_id])
    destination = relationship("Airport", foreign_keys=[destination_airport_id])

    def __repr__(self) -> str:  # pragma: no cover - representational
        return f"<Flight({self.flight_number} {self.origin_id}->{self.destination_id})>"


class FlightBookingStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class FlightBooking(Base):
    __tablename__ = "flight_bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    passengers = Column(Integer, default=1)
    cabin_class = Column(String(16), default="economy")  # economy, business, first
    status = Column(String(16), default=FlightBookingStatus.PENDING)

    total_price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    flight = relationship("Flight")


