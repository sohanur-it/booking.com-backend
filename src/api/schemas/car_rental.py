from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class CarSearch(BaseModel):
    pickup_city: str
    dropoff_city: Optional[str] = None
    pickup_datetime: datetime
    dropoff_datetime: datetime
    car_class: Optional[str] = None  # economy, compact, suv, premium
    transmission: Optional[str] = None  # automatic, manual
    air_conditioning: Optional[bool] = None
    seats_min: Optional[int] = None

    @field_validator("dropoff_datetime")
    def validate_dates(cls, v: datetime, values):
        if "pickup_datetime" in values and v <= values["pickup_datetime"]:
            raise ValueError("Dropoff must be after pickup")
        return v


class CarResponse(BaseModel):
    id: int
    vendor_id: int
    location_id: int
    make: str
    model: str
    car_class: str
    seats: int
    doors: int
    transmission: str
    air_conditioning: bool
    base_price_per_day: float
    currency: str

    class Config:
        from_attributes = True


class CarSearchResponse(BaseModel):
    cars: List[CarResponse]
    total_count: int


class CarBookingCreate(BaseModel):
    car_id: int
    pickup_datetime: datetime
    dropoff_datetime: datetime
    pickup_location_id: int
    dropoff_location_id: int


class CarBookingResponse(BaseModel):
    id: int
    user_id: int
    car_id: int
    pickup_datetime: datetime
    dropoff_datetime: datetime
    pickup_location_id: int
    dropoff_location_id: int
    status: str
    total_price: float
    currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


