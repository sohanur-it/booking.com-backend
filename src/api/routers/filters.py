from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.property import Property
from ..models.flight import Carrier
from ..models.car_rental import CarVendor, CarLocation
from ..schemas.filters import StaysFilterOptions, FlightFilterOptions, CarFilterOptions

router = APIRouter(prefix="/filters", tags=["Filters"])


@router.get("/stays", response_model=StaysFilterOptions)
def get_stays_filters(db: Session = Depends(get_db)):
    # Star ratings
    star_ratings = sorted({p.star_rating for p in db.query(Property.star_rating).all() if p.star_rating})
    # Property types
    property_types = sorted({p.property_type for p in db.query(Property.property_type).all() if p.property_type})
    # Amenities & facilities (flatten from JSON arrays)
    amenities = set()
    facilities = set()
    room_facilities = set()
    neighbourhoods = set()
    for p in db.query(Property).all():
        if p.amenities:
            for a in p.amenities:
                amenities.add(str(a))
        if p.facilities:
            for f in p.facilities:
                facilities.add(str(f))
        # For demo we reuse facilities as room facilities
        if p.facilities:
            for rf in p.facilities:
                room_facilities.add(str(rf))
        if p.neighbourhood:
            neighbourhoods.add(p.neighbourhood)

    policies = {
        "free_cancellation": True,
        "no_prepayment": True,
    }
    landmarks = ["beach", "city centre"]

    return StaysFilterOptions(
        star_ratings=star_ratings or [1, 2, 3, 4, 5],
        property_types=property_types or ["hotel", "apartment", "resort", "villa", "guest_house"],
        amenities=sorted(list(amenities)) or ["wifi", "pool", "spa", "fitness", "airport_shuttle"],
        facilities=sorted(list(facilities)) or ["beach_front", "business_center"],
        room_facilities=sorted(list(room_facilities)) or ["private_bathroom", "air_conditioning", "balcony", "kitchen"],
        policies=policies,
        landmarks=landmarks,
        neighbourhoods=sorted(list(neighbourhoods)),
    )


@router.get("/flights", response_model=FlightFilterOptions)
def get_flights_filters(db: Session = Depends(get_db)):
    carriers = [
        {"code": c.code, "name": c.name}
        for c in db.query(Carrier).all()
    ]
    return FlightFilterOptions(
        trip_types=["one_way", "round_trip"],
        cabin_classes=["economy", "business", "first"],
        carriers=carriers,
        stops=["nonstop", "1_stop_max"],
    )


@router.get("/cars", response_model=CarFilterOptions)
def get_cars_filters(db: Session = Depends(get_db)):
    vendors = [v.name for v in db.query(CarVendor).all()]
    locations = [f"{l.city}, {l.country}" for l in db.query(CarLocation).all()]
    return CarFilterOptions(
        vendors=vendors,
        car_classes=["economy", "compact", "suv", "premium"],
        transmissions=["automatic", "manual"],
        seats=[2, 4, 5, 7],
        locations=locations,
    )


