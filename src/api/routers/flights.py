from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from datetime import datetime

from ..database import get_db
from ..models.flight import Airport, Carrier, Flight, FlightBooking, FlightBookingStatus
from ..models.user import User
from ..schemas.flight import (
    FlightSearch, FlightSearchResponse, FlightResponse,
    FlightBookingCreate, FlightBookingResponse,
    AirportResponse, CarrierResponse, TripType,
    FlightListItem, RoundTripOption
)
from ..auth import get_current_active_user

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get("/airports", response_model=List[AirportResponse])
def list_airports(db: Session = Depends(get_db)):
    airports = db.query(Airport).all()
    return [AirportResponse.from_orm(a) for a in airports]


@router.get("/carriers", response_model=List[CarrierResponse])
def list_carriers(db: Session = Depends(get_db)):
    carriers = db.query(Carrier).all()
    return [CarrierResponse.from_orm(c) for c in carriers]


@router.get("/search", response_model=FlightSearchResponse)
def search_flights(
    origin_code: str = Query(...),
    destination_code: str = Query(...),
    departure_date: datetime = Query(...),
    return_date: datetime | None = Query(None),
    trip_type: TripType = Query(TripType.ONE_WAY),
    passengers: int = Query(1, ge=1),
    cabin_class: str = Query("economy"),
    nonstop_only: bool = Query(False),
    airline_codes: list[str] | None = Query(None),
    db: Session = Depends(get_db),
):
    origin = db.query(Airport).filter(Airport.code == origin_code).first()
    dest = db.query(Airport).filter(Airport.code == destination_code).first()
    if not origin or not dest:
        raise HTTPException(status_code=404, detail="Invalid origin or destination")

    # Simplified date filtering: same-day departures
    day_start = departure_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)

    query = db.query(Flight).filter(
        and_(
            Flight.origin_airport_id == origin.id,
            Flight.destination_airport_id == dest.id,
            Flight.departure_time >= day_start,
            Flight.departure_time <= day_end,
        )
    )
    if nonstop_only:
        query = query.filter(Flight.is_nonstop == True)
    if airline_codes:
        carriers = db.query(Carrier).filter(Carrier.code.in_(airline_codes)).all()
        carrier_ids = [c.id for c in carriers]
        if carrier_ids:
            query = query.filter(Flight.carrier_id.in_(carrier_ids))

    flights = query.all()

    # One-way list results enriched for UI
    items: list[FlightListItem] = []
    for f in flights:
        carrier = db.query(Carrier).filter(Carrier.id == f.carrier_id).first()
        items.append(FlightListItem(
            **FlightResponse.from_orm(f).dict(),
            carrier_code=carrier.code if carrier else None,
            carrier_name=carrier.name if carrier else None,
            stops_count=0 if f.is_nonstop else 1,
        ))

    if trip_type == TripType.ONE_WAY or not return_date:
        return FlightSearchResponse(flights=items, total_count=len(items))

    # Round trip: pair outbound with return flights
    ret_day_start = return_date.replace(hour=0, minute=0, second=0, microsecond=0)
    ret_day_end = ret_day_start.replace(hour=23, minute=59, second=59, microsecond=999999)
    ret_query = db.query(Flight).filter(
        and_(
            Flight.origin_airport_id == dest.id,
            Flight.destination_airport_id == origin.id,
            Flight.departure_time >= ret_day_start,
            Flight.departure_time <= ret_day_end,
        )
    )
    if nonstop_only:
        ret_query = ret_query.filter(Flight.is_nonstop == True)
    if airline_codes:
        ret_query = ret_query.filter(Flight.carrier_id.in_(carrier_ids))
    returns = ret_query.all()

    ret_items: list[FlightListItem] = []
    for f in returns:
        carrier = db.query(Carrier).filter(Carrier.id == f.carrier_id).first()
        ret_items.append(FlightListItem(
            **FlightResponse.from_orm(f).dict(),
            carrier_code=carrier.code if carrier else None,
            carrier_name=carrier.name if carrier else None,
            stops_count=0 if f.is_nonstop else 1,
        ))

    # Simple Cartesian pairing; in production apply time windows and price combos
    pairs: list[RoundTripOption] = []
    for o in items:
        for r in ret_items:
            total_price = o.base_price * passengers + r.base_price * passengers
            pairs.append(RoundTripOption(outbound=o, return_flight=r, total_price=total_price))

    return FlightSearchResponse(round_trip_options=pairs, total_count=len(pairs))


@router.post("/book", response_model=FlightBookingResponse)
def book_flight(
    booking: FlightBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    flight = db.query(Flight).filter(Flight.id == booking.flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    # Capacity check (very simplified per cabin)
    if booking.cabin_class == "economy" and flight.seats_economy < booking.passengers:
        raise HTTPException(status_code=400, detail="Not enough economy seats")
    if booking.cabin_class == "business" and flight.seats_business < booking.passengers:
        raise HTTPException(status_code=400, detail="Not enough business seats")
    if booking.cabin_class == "first" and flight.seats_first < booking.passengers:
        raise HTTPException(status_code=400, detail="Not enough first-class seats")

    total_price = flight.base_price * booking.passengers

    db_booking = FlightBooking(
        user_id=current_user.id,
        flight_id=flight.id,
        passengers=booking.passengers,
        cabin_class=booking.cabin_class,
        status=FlightBookingStatus.PENDING,
        total_price=total_price,
        currency=flight.currency,
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return FlightBookingResponse.from_orm(db_booking)


@router.put("/bookings/{booking_id}", response_model=FlightBookingResponse)
def update_flight_booking(
    booking_id: int,
    booking: FlightBookingCreate,  # simple reuse for demo: passengers/cabin_class
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    fb = db.query(FlightBooking).filter(FlightBooking.id == booking_id, FlightBooking.user_id == current_user.id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Booking not found")
    fb.passengers = booking.passengers
    fb.cabin_class = booking.cabin_class
    # Recalculate price (simplified)
    flight = db.query(Flight).filter(Flight.id == fb.flight_id).first()
    fb.total_price = (flight.base_price if flight else fb.total_price) * booking.passengers
    db.commit()
    db.refresh(fb)
    return FlightBookingResponse.from_orm(fb)



