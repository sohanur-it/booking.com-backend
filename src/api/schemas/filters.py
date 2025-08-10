from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class StaysFilterOptions(BaseModel):
    star_ratings: List[int]
    property_types: List[str]
    amenities: List[str]
    facilities: List[str]
    room_facilities: List[str]
    policies: Dict[str, bool]
    landmarks: List[str]
    neighbourhoods: List[str]


class FlightFilterOptions(BaseModel):
    trip_types: List[str]
    cabin_classes: List[str]
    carriers: List[Dict[str, str]]  # { code, name }
    stops: List[str]


class CarFilterOptions(BaseModel):
    vendors: List[str]
    car_classes: List[str]
    transmissions: List[str]
    seats: List[int]
    locations: List[str]


