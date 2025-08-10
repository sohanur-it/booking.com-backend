from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, time
from enum import Enum


class AirportResponse(BaseModel):
    id: int
    code: str
    name: str
    city: str
    country: str

    class Config:
        from_attributes = True


class CarrierResponse(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True


class TripType(str, Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class FlightSearch(BaseModel):
    origin_code: str
    destination_code: str
    departure_date: datetime
    return_date: Optional[datetime] = None
    trip_type: TripType = TripType.ONE_WAY
    passengers: int = 1
    cabin_class: str = "economy"
    nonstop_only: bool = False
    airline_codes: Optional[List[str]] = None
    depart_time_from: Optional[time] = None
    depart_time_to: Optional[time] = None
    sort_by: Optional[str] = "best"  # best, cheapest, fastest

    @field_validator("passengers")
    def validate_passengers(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Passengers must be >= 1")
        return v


class FlightResponse(BaseModel):
    id: int
    carrier_id: int
    flight_number: str
    origin_airport_id: int
    destination_airport_id: int
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    is_nonstop: bool
    base_price: float
    currency: str

    class Config:
        from_attributes = True


class FlightListItem(FlightResponse):
    carrier_code: Optional[str] = None
    carrier_name: Optional[str] = None
    stops_count: int = 0


class RoundTripOption(BaseModel):
    outbound: FlightListItem
    return_flight: FlightListItem
    total_price: float


class FlightSearchResponse(BaseModel):
    flights: Optional[List[FlightListItem]] = None
    round_trip_options: Optional[List[RoundTripOption]] = None
    total_count: int


class FlightBookingCreate(BaseModel):
    flight_id: int
    passengers: int = 1
    cabin_class: str = "economy"

    @field_validator("passengers")
    def validate_passengers(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Passengers must be >= 1")
        return v


class FlightBookingResponse(BaseModel):
    id: int
    user_id: int
    flight_id: int
    passengers: int
    cabin_class: str
    status: str
    total_price: float
    currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


