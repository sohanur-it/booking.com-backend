from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List
from datetime import datetime

from ..database import get_db
from ..models.car_rental import (
    CarVendor, CarLocation, Car, CarBooking, CarBookingStatus
)
from ..schemas.car_rental import (
    CarSearch, CarSearchResponse, CarResponse,
    CarBookingCreate, CarBookingResponse
)
from ..auth import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/cars", tags=["Car Rentals"])


@router.get("/locations", response_model=List[str])
def list_locations(db: Session = Depends(get_db)):
    locs = db.query(CarLocation).all()
    return [f"{l.city}, {l.country}" for l in locs]


@router.get("/search", response_model=CarSearchResponse)
def search_cars(
    pickup_city: str = Query(...),
    dropoff_city: str | None = Query(None),
    pickup_datetime: datetime = Query(...),
    dropoff_datetime: datetime = Query(...),
    car_class: str | None = Query(None),
    transmission: str | None = Query(None),
    air_conditioning: bool | None = Query(None),
    seats_min: int | None = Query(None),
    db: Session = Depends(get_db),
):
    pickup_locs = db.query(CarLocation).filter(CarLocation.city.ilike(f"%{pickup_city}%")).all()
    if not pickup_locs:
        return CarSearchResponse(cars=[], total_count=0)

    loc_ids = [l.id for l in pickup_locs]
    query = db.query(Car).filter(Car.location_id.in_(loc_ids))
    if car_class:
        query = query.filter(Car.car_class == car_class)
    if transmission:
        query = query.filter(Car.transmission == transmission)
    if air_conditioning is not None:
        query = query.filter(Car.air_conditioning == air_conditioning)
    if seats_min is not None:
        query = query.filter(Car.seats >= seats_min)

    cars = query.all()
    return CarSearchResponse(cars=[CarResponse.from_orm(c) for c in cars], total_count=len(cars))


@router.post("/book", response_model=CarBookingResponse)
def book_car(
    booking: CarBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    car = db.query(Car).filter(Car.id == booking.car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # Simple overlapping rental count
    overlapping = db.query(CarBooking).filter(
        and_(
            CarBooking.car_id == car.id,
            CarBooking.status.in_([CarBookingStatus.PENDING, CarBookingStatus.CONFIRMED]),
            CarBooking.pickup_datetime < booking.dropoff_datetime,
            CarBooking.dropoff_datetime > booking.pickup_datetime,
        )
    ).count()
    available = max(0, car.available_quantity - overlapping)
    if available < 1:
        raise HTTPException(status_code=400, detail="Car not available for selected dates")

    days = max(1, (booking.dropoff_datetime - booking.pickup_datetime).days)
    total_price = days * car.base_price_per_day

    db_booking = CarBooking(
        user_id=current_user.id,
        car_id=car.id,
        pickup_datetime=booking.pickup_datetime,
        dropoff_datetime=booking.dropoff_datetime,
        pickup_location_id=booking.pickup_location_id,
        dropoff_location_id=booking.dropoff_location_id,
        status=CarBookingStatus.PENDING,
        total_price=total_price,
        currency=car.currency,
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return CarBookingResponse.from_orm(db_booking)


@router.delete("/bookings/{booking_id}")
def cancel_car_booking(booking_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    cb = db.query(CarBooking).filter(CarBooking.id == booking_id, CarBooking.user_id == current_user.id).first()
    if not cb:
        raise HTTPException(status_code=404, detail="Booking not found")
    if cb.status == CarBookingStatus.CANCELLED:
        return {"message": "Already cancelled"}
    cb.status = CarBookingStatus.CANCELLED
    db.commit()
    return {"message": "Cancelled"}



