"""
Data seeding script for Booking.com clone backend.
Run this script to populate the database with sample data for testing.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from pathlib import Path

from .database import SessionLocal, engine
from .models.user import User
from .models.property import Property, Room, RoomRate
from .models.booking import Booking, BookingStatus, PaymentStatus, PaymentMethod
from .models.review import Review, ReviewResponse
from .models.flight import Airport, Carrier, Flight
from .models.car_rental import CarVendor, CarLocation, Car
from .models.metadata import FacilityCode
from .auth import get_password_hash

def _load_json(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def seed_from_json(data_dir: str | Path | None = None):
    """Seed the database using JSON files placed in a directory.

    Files supported (all optional):
      - facility_codes.json
      - users.json
      - properties.json (can include nested rooms under each property)
      - rooms.json
      - bookings.json
      - reviews.json
      - payment_methods.json
      - airports.json, carriers.json, flights.json
      - car_vendors.json, car_locations.json, cars.json
    """
    base_dir = Path(data_dir) if data_dir else Path(__file__).parent / "seed_json"
    db = SessionLocal()
    base_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Facility codes
        facility_codes = _load_json(base_dir / "facility_codes.json") or []
        for fc in facility_codes:
            if not db.query(FacilityCode).filter(FacilityCode.code == fc["code"]).first():
                db.add(FacilityCode(code=fc["code"], label=fc["label"], scope=fc.get("scope", "property")))
        db.commit()

        # Users
        users = _load_json(base_dir / "users.json") or []
        for u in users:
            if not db.query(User).filter(User.email == u["email"]).first():
                db.add(User(
                    email=u["email"],
                    password_hash=get_password_hash(u.get("password", "password123")),
                    first_name=u.get("first_name", ""),
                    last_name=u.get("last_name", ""),
                    phone=u.get("phone"),
                    is_verified=u.get("is_verified", True),
                    genius_level=u.get("genius_level", 0),
                    total_bookings=u.get("total_bookings", 0),
                    total_spent=u.get("total_spent", 0.0),
                    genius_discount_percentage=u.get("genius_discount_percentage", 0.0),
                ))
        db.commit()

        # Properties (with optional nested rooms)
        properties = _load_json(base_dir / "properties.json") or []
        for p in properties:
            existing = db.query(Property).filter(Property.name == p["name"]).first()
            if not existing:
                existing = Property(
                    name=p["name"], description=p.get("description"), address=p["address"],
                    city=p["city"], country=p["country"], postal_code=p.get("postal_code"),
                    latitude=p.get("latitude"), longitude=p.get("longitude"),
                    property_type=p.get("property_type"), star_rating=p.get("star_rating"),
                    total_rooms=p.get("total_rooms"), phone=p.get("phone"), email=p.get("email"),
                    website=p.get("website"), amenities=p.get("amenities"), facilities=p.get("facilities"),
                    base_price=p.get("base_price"), currency=p.get("currency", "USD"),
                    images=p.get("images"), is_active=p.get("is_active", True),
                    supports_free_cancellation=p.get("supports_free_cancellation", True),
                    supports_no_prepayment=p.get("supports_no_prepayment", False),
                    neighbourhood=p.get("neighbourhood"),
                )
                db.add(existing)
                db.commit(); db.refresh(existing)
            # Nested rooms
            for r in p.get("rooms", []):
                if not db.query(Room).filter(Room.property_id == existing.id, Room.name == r["name"]).first():
                    db.add(Room(
                        property_id=existing.id,
                        name=r["name"], description=r.get("description"), room_type=r.get("room_type"),
                        max_guests=r.get("max_guests", 2), size_sqm=r.get("size_sqm"),
                        room_amenities=r.get("room_amenities"), base_price=r.get("base_price", 100.0),
                        genius_price=r.get("genius_price"), total_quantity=r.get("total_quantity", 1),
                        available_quantity=r.get("available_quantity", 1), images=r.get("images"),
                    ))
            db.commit()

            # Nested room rates (if provided)
            for r in p.get("rooms", []):
                rates = r.get("rates", [])
                if not rates:
                    continue
                room_obj = db.query(Room).filter(Room.property_id == existing.id, Room.name == r["name"]).first()
                if not room_obj:
                    continue
                for rate in rates:
                    if not db.query(RoomRate).filter(RoomRate.room_id == room_obj.id, RoomRate.name == rate["name"]).first():
                        db.add(RoomRate(
                            room_id=room_obj.id,
                            name=rate["name"],
                            description=rate.get("description"),
                            price=rate.get("price", room_obj.base_price or 0.0),
                            currency=rate.get("currency", "USD"),
                            includes_breakfast=rate.get("includes_breakfast", False),
                            includes_parking=rate.get("includes_parking", False),
                            free_cancellation=rate.get("free_cancellation", False),
                            refundable_until=datetime.fromisoformat(rate["refundable_until"]) if rate.get("refundable_until") else None,
                            pay_at_property=rate.get("pay_at_property", False),
                        ))
                db.commit()

        # Standalone rooms file
        rooms = _load_json(base_dir / "rooms.json") or []
        for r in rooms:
            prop = db.query(Property).filter(Property.name == r["property_name"]).first()
            if prop and not db.query(Room).filter(Room.property_id == prop.id, Room.name == r["name"]).first():
                db.add(Room(
                    property_id=prop.id,
                    name=r["name"], description=r.get("description"), room_type=r.get("room_type"),
                    max_guests=r.get("max_guests", 2), size_sqm=r.get("size_sqm"),
                    room_amenities=r.get("room_amenities"), base_price=r.get("base_price", 100.0),
                    genius_price=r.get("genius_price"), total_quantity=r.get("total_quantity", 1),
                    available_quantity=r.get("available_quantity", 1), images=r.get("images"),
                ))
        db.commit()

        # Room rates for standalone rooms.json (if provided)
        for r in rooms:
            if not r.get("rates"):
                continue
            prop = db.query(Property).filter(Property.name == r.get("property_name")).first()
            if not prop:
                continue
            room_obj = db.query(Room).filter(Room.property_id == prop.id, Room.name == r["name"]).first()
            if not room_obj:
                continue
            for rate in r["rates"]:
                if not db.query(RoomRate).filter(RoomRate.room_id == room_obj.id, RoomRate.name == rate["name"]).first():
                    db.add(RoomRate(
                        room_id=room_obj.id,
                        name=rate["name"],
                        description=rate.get("description"),
                        price=rate.get("price", room_obj.base_price or 0.0),
                        currency=rate.get("currency", "USD"),
                        includes_breakfast=rate.get("includes_breakfast", False),
                        includes_parking=rate.get("includes_parking", False),
                        free_cancellation=rate.get("free_cancellation", False),
                        refundable_until=datetime.fromisoformat(rate["refundable_until"]) if rate.get("refundable_until") else None,
                        pay_at_property=rate.get("pay_at_property", False),
                    ))
            db.commit()

        # Airports, carriers, flights
        for a in _load_json(base_dir / "airports.json") or []:
            if not db.query(Airport).filter(Airport.code == a["code"]).first():
                db.add(Airport(code=a["code"], name=a["name"], city=a["city"], country=a["country"], latitude=a.get("latitude"), longitude=a.get("longitude")))
        for c in _load_json(base_dir / "carriers.json") or []:
            if not db.query(Carrier).filter(Carrier.code == c["code"]).first():
                db.add(Carrier(code=c["code"], name=c["name"]))
        db.commit()
        for f in _load_json(base_dir / "flights.json") or []:
            if not db.query(Flight).filter(Flight.flight_number == f["flight_number"]).first():
                carrier = db.query(Carrier).filter(Carrier.code == f["carrier_code"]).first()
                origin = db.query(Airport).filter(Airport.code == f["origin_code"]).first()
                dest = db.query(Airport).filter(Airport.code == f["destination_code"]).first()
                if carrier and origin and dest:
                    db.add(Flight(
                        carrier_id=carrier.id,
                        flight_number=f["flight_number"],
                        origin_airport_id=origin.id,
                        destination_airport_id=dest.id,
                        departure_time=datetime.fromisoformat(f["departure_time"]),
                        arrival_time=datetime.fromisoformat(f["arrival_time"]),
                        duration_minutes=f.get("duration_minutes", 0),
                        is_nonstop=f.get("is_nonstop", True),
                        base_price=f.get("base_price", 0.0),
                        currency=f.get("currency", "USD"),
                        seats_economy=f.get("seats_economy", 0),
                        seats_business=f.get("seats_business", 0),
                        seats_first=f.get("seats_first", 0),
                    ))
        db.commit()

        # Car vendors, locations, cars
        for v in _load_json(base_dir / "car_vendors.json") or []:
            if not db.query(CarVendor).filter(CarVendor.code == v["code"]).first():
                db.add(CarVendor(code=v["code"], name=v["name"]))
        db.commit()
        locs = _load_json(base_dir / "car_locations.json") or []
        for l in locs:
            exists = db.query(CarLocation).filter(CarLocation.city == l["city"], CarLocation.airport_code == l.get("airport_code")).first()
            if not exists:
                db.add(CarLocation(city=l["city"], country=l["country"], airport_code=l.get("airport_code"), address=l.get("address"), latitude=l.get("latitude"), longitude=l.get("longitude")))
        db.commit()
        cars = _load_json(base_dir / "cars.json") or []
        for c in cars:
            vendor = db.query(CarVendor).filter(CarVendor.code == c["vendor_code"]).first()
            loc = db.query(CarLocation).filter(CarLocation.city == c["location_city"]).first()
            exists = None
            if vendor and loc:
                exists = db.query(Car).filter(Car.location_id == loc.id, Car.make == c["make"], Car.model == c["model"]).first()
                if not exists:
                    db.add(Car(
                        vendor_id=vendor.id, location_id=loc.id,
                        make=c["make"], model=c["model"], car_class=c.get("car_class", "economy"),
                        seats=c.get("seats", 4), doors=c.get("doors", 4), transmission=c.get("transmission", "automatic"),
                        air_conditioning=c.get("air_conditioning", True), base_price_per_day=c.get("base_price_per_day", 0.0),
                        currency=c.get("currency", "USD"), available_quantity=c.get("available_quantity", 1),
                    ))
        db.commit()

        # Payment methods
        for pm in _load_json(base_dir / "payment_methods.json") or []:
            user = db.query(User).filter(User.email == pm["user_email"]).first()
            if user and not db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id, PaymentMethod.last_four_digits == pm["last_four_digits"]).first():
                db.add(PaymentMethod(
                    user_id=user.id, method_type=pm["method_type"], card_type=pm.get("card_type"), last_four_digits=pm["last_four_digits"],
                    expiry_month=pm["expiry_month"], expiry_year=pm["expiry_year"], cardholder_name=pm["cardholder_name"],
                    is_default=pm.get("is_default", False), is_active=pm.get("is_active", True),
                ))
        db.commit()

        # Bookings
        for b in _load_json(base_dir / "bookings.json") or []:
            if not db.query(Booking).filter(Booking.booking_reference == b.get("booking_reference")).first():
                user = db.query(User).filter(User.email == b["user_email"]).first()
                room = None
                if b.get("room_name") and b.get("property_name"):
                    prop = db.query(Property).filter(Property.name == b["property_name"]).first()
                    if prop:
                        room = db.query(Room).filter(Room.property_id == prop.id, Room.name == b["room_name"]).first()
                if user and room:
                    db.add(Booking(
                        booking_reference=b.get("booking_reference", f"BK-{datetime.now().strftime('%Y%m%d')}-JSON"),
                        user_id=user.id, room_id=room.id,
                        check_in_date=datetime.fromisoformat(b["check_in_date"]),
                        check_out_date=datetime.fromisoformat(b["check_out_date"]),
                        num_guests=b.get("num_guests", 1), num_rooms=b.get("num_rooms", 1),
                        guest_names=b.get("guest_names"), special_requests=b.get("special_requests"),
                        base_price=b.get("base_price", 0.0), genius_discount=b.get("genius_discount", 0.0),
                        taxes=b.get("taxes", 0.0), total_price=b.get("total_price", 0.0), currency=b.get("currency", "USD"),
                        free_cancellation=b.get("free_cancellation", True), cancellation_deadline=datetime.fromisoformat(b["cancellation_deadline"]) if b.get("cancellation_deadline") else None,
                        cancellation_fee=b.get("cancellation_fee", 0.0), status=b.get("status", BookingStatus.PENDING),
                        payment_status=b.get("payment_status", PaymentStatus.PENDING), confirmed_at=datetime.fromisoformat(b["confirmed_at"]) if b.get("confirmed_at") else None,
                        cancelled_at=datetime.fromisoformat(b["cancelled_at"]) if b.get("cancelled_at") else None,
                    ))
        db.commit()

        # Reviews
        for rv in _load_json(base_dir / "reviews.json") or []:
            user = db.query(User).filter(User.email == rv["user_email"]).first()
            prop = db.query(Property).filter(Property.name == rv["property_name"]).first()
            booking = db.query(Booking).filter(Booking.booking_reference == rv.get("booking_reference")).first() if rv.get("booking_reference") else None
            if user and prop and booking and not db.query(Review).filter(Review.booking_id == booking.id, Review.user_id == user.id).first():
                db.add(Review(
                    user_id=user.id, property_id=prop.id, booking_id=booking.id, title=rv.get("title"), content=rv["content"],
                    overall_rating=rv["overall_rating"], cleanliness_rating=rv.get("cleanliness_rating"), comfort_rating=rv.get("comfort_rating"),
                    location_rating=rv.get("location_rating"), facilities_rating=rv.get("facilities_rating"), staff_rating=rv.get("staff_rating"),
                    value_for_money_rating=rv.get("value_for_money_rating"), wifi_rating=rv.get("wifi_rating"), is_verified_stay=rv.get("is_verified_stay", True),
                    helpful_votes=rv.get("helpful_votes", 0), is_helpful=rv.get("is_helpful", False), is_approved=rv.get("is_approved", True),
                ))
        db.commit()

        print(f"JSON seeding completed from {base_dir}")
    except Exception as e:
        print(f"Error seeding from JSON: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def seed_database():
    """Seed the database with sample data. If seed_json directory exists and contains files, use it."""
    # First try JSON-driven seeding
    try:
        seed_from_json()
        return
    except Exception:
        # fall back to programmatic sample seeding
        pass
    db = SessionLocal()
    try:
        # Create sample users
        print("Creating sample users...")
        
        # Users (idempotent)
        def get_or_create_user(email: str, **kwargs) -> User:
            u = db.query(User).filter(User.email == email).first()
            if u:
                return u
            u = User(email=email, **kwargs)
            db.add(u)
            db.commit()
            db.refresh(u)
            return u

        user1 = get_or_create_user(
            email="john.doe@example.com",
            password_hash=get_password_hash("password123"),
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            is_verified=True,
            genius_level=2,
            total_bookings=7,
            total_spent=2500.0,
            genius_discount_percentage=15.0,
        )
        user2 = get_or_create_user(
            email="jane.smith@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Jane",
            last_name="Smith",
            phone="+1987654321",
            is_verified=True,
            genius_level=1,
            total_bookings=3,
            total_spent=800.0,
            genius_discount_percentage=10.0,
        )
        user3 = get_or_create_user(
            email="mike.johnson@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Mike",
            last_name="Johnson",
            phone="+1555123456",
            is_verified=True,
            genius_level=3,
            total_bookings=20,
            total_spent=7500.0,
            genius_discount_percentage=20.0,
        )
        
        # Create sample properties
        print("Creating sample properties...")
        
        def get_or_create_property(name: str, **kwargs) -> Property:
            p = db.query(Property).filter(Property.name == name).first()
            if p:
                return p
            p = Property(name=name, **kwargs)
            db.add(p)
            db.commit()
            db.refresh(p)
            return p

        # Property 1 - Luxury Hotel
        property1 = get_or_create_property(
        name="The Grand Plaza Hotel",
        description="A luxurious 5-star hotel in the heart of downtown with stunning city views and world-class amenities.",
        address="123 Main Street",
        city="New York",
        country="United States",
        postal_code="10001",
        latitude=40.7589,
        longitude=-73.9851,
        property_type="hotel",
        star_rating=5,
        total_rooms=200,
        phone="+1-555-123-4567",
        email="info@grandplaza.com",
        website="https://grandplaza.com",
        amenities=["wifi", "pool", "gym", "spa", "restaurant", "bar", "concierge", "valet_parking"],
        facilities=["business_center", "meeting_rooms", "fitness_center", "swimming_pool", "spa_center"],
        base_price=300.0,
        currency="USD",
        supports_free_cancellation=True,
        supports_no_prepayment=False,
        neighbourhood="Midtown",
        images=[
            "https://example.com/grand-plaza-1.jpg",
            "https://example.com/grand-plaza-2.jpg",
            "https://example.com/grand-plaza-3.jpg"
        ],
        rooms=[
            {
                "name": "Deluxe King Room",
                "room_type": "king",
                "max_guests": 2,
                "size_sqm": 45.0,
                "room_amenities": ["private_bathroom", "air_conditioning"],
                "base_price": 300.0,
                "genius_price": 255.0,
                "total_quantity": 50,
                "available_quantity": 45,
                "images": ["https://example.com/deluxe-king-1.jpg"],
                "rates": [
                    {
                        "name": "Non-refundable",
                        "description": "Cheaper rate with no refund if canceled",
                        "price": 280.0,
                        "currency": "USD",
                        "includes_breakfast": False,
                        "includes_parking": False,
                        "free_cancellation": False,
                        "refundable_until": None,
                        "pay_at_property": False
                    },
                    {
                        "name": "Breakfast included",
                        "description": "Includes breakfast and free cancellation up to 24h before",
                        "price": 320.0,
                        "currency": "USD",
                        "includes_breakfast": True,
                        "includes_parking": False,
                        "free_cancellation": True,
                        "refundable_until": "2025-12-01T12:00:00",
                        "pay_at_property": True
                    }
                ]
            }
        ]
    )

        
        # Property 2 - Boutique Hotel
        property2 = get_or_create_property(
            name="The Cozy Inn",
            description="A charming boutique hotel with personalized service and unique character.",
            address="456 Oak Avenue",
            city="San Francisco",
            country="United States",
            postal_code="94102",
            latitude=37.7749,
            longitude=-122.4194,
            property_type="boutique_hotel",
            star_rating=4,
            total_rooms=50,
            phone="+1-555-987-6543",
            email="hello@cozyinn.com",
            website="https://cozyinn.com",
            amenities=["wifi", "breakfast", "garden", "terrace"],
            facilities=["lounge", "garden_area", "breakfast_room"],
            base_price=180.0,
            currency="USD",
            images=[
                "https://example.com/cozy-inn-1.jpg",
                "https://example.com/cozy-inn-2.jpg"
            ]
        )
        
        # Property 3 - Resort
        property3 = get_or_create_property(
            name="Paradise Beach Resort",
            description="An all-inclusive beachfront resort with private beach access and tropical paradise setting.",
            address="789 Beach Road",
            city="Miami",
            country="United States",
            postal_code="33139",
            latitude=25.7617,
            longitude=-80.1918,
            property_type="resort",
            star_rating=4,
            total_rooms=150,
            phone="+1-555-456-7890",
            email="reservations@paradisebeach.com",
            website="https://paradisebeach.com",
            amenities=["wifi", "pool", "beach_access", "spa", "restaurant", "bar", "kids_club", "water_sports"],
            facilities=["beach_front", "swimming_pools", "spa_center", "multiple_restaurants", "water_sports_center"],
            base_price=250.0,
            currency="USD",
            images=[
                "https://example.com/paradise-beach-1.jpg",
                "https://example.com/paradise-beach-2.jpg",
                "https://example.com/paradise-beach-3.jpg"
            ]
        )
        
        # Create sample rooms
        print("Creating sample rooms...")
        
        # Rooms for Property 1
        def get_or_create_room(property_id: int, name: str, **kwargs) -> Room:
            r = db.query(Room).filter(Room.property_id == property_id, Room.name == name).first()
            if r:
                return r
            r = Room(property_id=property_id, name=name, **kwargs)
            db.add(r)
            db.commit()
            db.refresh(r)
            return r

        room1_1 = get_or_create_room(
            property_id=property1.id,
            name="Deluxe King Room",
            description="Spacious king room with city view and luxury amenities.",
            room_type="king",
            max_guests=2,
            size_sqm=45.0,
            room_amenities=["king_bed", "city_view", "minibar", "coffee_maker", "bathrobe"],
            base_price=300.0,
            genius_price=255.0,
            total_quantity=50,
            available_quantity=45,
            images=["https://example.com/deluxe-king-1.jpg", "https://example.com/deluxe-king-2.jpg"]
        )
        
        room1_2 = get_or_create_room(
            property_id=property1.id,
            name="Executive Suite",
            description="Luxury suite with separate living area and premium services.",
            room_type="suite",
            max_guests=4,
            size_sqm=80.0,
            room_amenities=["king_bed", "sofa_bed", "living_room", "balcony", "butler_service"],
            base_price=500.0,
            genius_price=425.0,
            total_quantity=20,
            available_quantity=18,
            images=["https://example.com/executive-suite-1.jpg"]
        )
        
        # Rooms for Property 2
        room2_1 = get_or_create_room(
            property_id=property2.id,
            name="Cozy Queen Room",
            description="Comfortable queen room with garden view.",
            room_type="queen",
            max_guests=2,
            size_sqm=35.0,
            room_amenities=["queen_bed", "garden_view", "coffee_maker"],
            base_price=180.0,
            genius_price=162.0,
            total_quantity=30,
            available_quantity=28,
            images=["https://example.com/cozy-queen-1.jpg"]
        )
        
        # Rooms for Property 3
        room3_1 = get_or_create_room(
            property_id=property3.id,
            name="Ocean View Room",
            description="Beautiful room with direct ocean view and balcony.",
            room_type="king",
            max_guests=2,
            size_sqm=50.0,
            room_amenities=["king_bed", "ocean_view", "balcony", "minibar"],
            base_price=250.0,
            genius_price=212.5,
            total_quantity=100,
            available_quantity=95,
            images=["https://example.com/ocean-view-1.jpg", "https://example.com/ocean-view-2.jpg"]
        )

        # Create sample room rates
        def get_or_create_rate(room_id: int, name: str, **kwargs) -> RoomRate:
            rr = db.query(RoomRate).filter(RoomRate.room_id == room_id, RoomRate.name == name).first()
            if rr:
                return rr
            rr = RoomRate(room_id=room_id, name=name, **kwargs)
            db.add(rr)
            db.commit()
            db.refresh(rr)
            return rr

        # Rates for Property 1 - Deluxe King Room
        get_or_create_rate(
            room_id=room1_1.id,
            name="Non-refundable",
            description="Cheaper rate with no refund if canceled",
            price=280.0,
            currency="USD",
            includes_breakfast=False,
            includes_parking=False,
            free_cancellation=False,
            refundable_until=None,
            pay_at_property=False,
        )
        get_or_create_rate(
            room_id=room1_1.id,
            name="Breakfast included",
            description="Includes breakfast and free cancellation up to 24h before",
            price=320.0,
            currency="USD",
            includes_breakfast=True,
            includes_parking=False,
            free_cancellation=True,
            refundable_until=datetime.now() + timedelta(days=120),
            pay_at_property=True,
        )

        # Example rate for Executive Suite
        get_or_create_rate(
            room_id=room1_2.id,
            name="Flexible rate",
            description="Free cancellation until 2 days before arrival",
            price=520.0,
            currency="USD",
            includes_breakfast=False,
            includes_parking=False,
            free_cancellation=True,
            refundable_until=datetime.now() + timedelta(days=60),
            pay_at_property=True,
        )

        # Example rate for Ocean View Room
        get_or_create_rate(
            room_id=room3_1.id,
            name="Early bird",
            description="Non-refundable early booking discount",
            price=230.0,
            currency="USD",
            includes_breakfast=False,
            includes_parking=False,
            free_cancellation=False,
            refundable_until=None,
            pay_at_property=False,
        )
        
        # Create sample bookings
        print("Creating sample bookings...")
        
        # Past booking for user1
        def get_or_create_booking(reference: str, **kwargs) -> Booking:
            b = db.query(Booking).filter(Booking.booking_reference == reference).first()
            if b:
                return b
            b = Booking(booking_reference=reference, **kwargs)
            db.add(b)
            db.commit()
            db.refresh(b)
            return b

        booking1 = get_or_create_booking(
            reference="BK-20241201-ABC12",
            user_id=user1.id,
            room_id=room1_1.id,
            check_in_date=datetime.now() - timedelta(days=30),
            check_out_date=datetime.now() - timedelta(days=25),
            num_guests=2,
            num_rooms=1,
            guest_names=["John Doe", "Jane Doe"],
            special_requests="Early check-in if possible",
            base_price=1500.0,
            genius_discount=225.0,
            taxes=127.5,
            total_price=1402.5,
            currency="USD",
            free_cancellation=True,
            cancellation_deadline=datetime.now() - timedelta(days=31),
            cancellation_fee=0.0,
            status=BookingStatus.COMPLETED,
            payment_status=PaymentStatus.PAID,
            confirmed_at=datetime.now() - timedelta(days=35),
        )
        
        # Current booking for user2
        booking2 = get_or_create_booking(
            reference="BK-20241201-DEF34",
            user_id=user2.id,
            room_id=room2_1.id,
            check_in_date=datetime.now() + timedelta(days=5),
            check_out_date=datetime.now() + timedelta(days=10),
            num_guests=2,
            num_rooms=1,
            guest_names=["Jane Smith", "Bob Smith"],
            base_price=900.0,
            genius_discount=90.0,
            taxes=81.0,
            total_price=891.0,
            currency="USD",
            free_cancellation=True,
            cancellation_deadline=datetime.now() + timedelta(days=4),
            cancellation_fee=0.0,
            status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            confirmed_at=datetime.now() - timedelta(days=10),
        )
        
        # Create sample reviews
        print("Creating sample reviews...")
        
        if not db.query(Review).filter(Review.booking_id == booking1.id, Review.user_id == user1.id).first():
            review1 = Review(
                user_id=user1.id,
                property_id=property1.id,
                booking_id=booking1.id,
                title="Excellent luxury experience!",
                content="The Grand Plaza Hotel exceeded all expectations. The room was spacious and luxurious, the staff was incredibly attentive, and the location was perfect for exploring the city. The Genius discount made it even better value for money.",
                overall_rating=9.5,
                cleanliness_rating=9.5,
                comfort_rating=9.0,
                location_rating=10.0,
                facilities_rating=9.0,
                staff_rating=9.5,
                value_for_money_rating=9.0,
                wifi_rating=9.5,
                is_verified_stay=True,
                helpful_votes=12,
                is_helpful=True,
                is_approved=True,
            )
            db.add(review1)
            db.commit()
        
        # Create sample payment methods
        print("Creating sample payment methods...")
        
        if not db.query(PaymentMethod).filter(PaymentMethod.user_id == user1.id, PaymentMethod.last_four_digits == "1234").first():
            payment_method1 = PaymentMethod(
                user_id=user1.id,
                method_type="credit_card",
                card_type="visa",
                last_four_digits="1234",
                expiry_month=12,
                expiry_year=2025,
                cardholder_name="John Doe",
                is_default=True,
                is_active=True,
            )
            db.add(payment_method1)
            db.commit()
        if not db.query(PaymentMethod).filter(PaymentMethod.user_id == user2.id, PaymentMethod.last_four_digits == "5678").first():
            payment_method2 = PaymentMethod(
                user_id=user2.id,
                method_type="credit_card",
                card_type="mastercard",
                last_four_digits="5678",
                expiry_month=8,
                expiry_year=2026,
                cardholder_name="Jane Smith",
                is_default=True,
                is_active=True,
            )
            db.add(payment_method2)
            db.commit()
        
        print("Database seeded successfully!")
        print(f"Created {db.query(User).count()} users")
        print(f"Created {db.query(Property).count()} properties")
        print(f"Created {db.query(Room).count()} rooms")
        print(f"Created {db.query(Booking).count()} bookings")
        print(f"Created {db.query(Review).count()} reviews")
        print(f"Created {db.query(PaymentMethod).count()} payment methods")
        from sqlalchemy import func as _func
        print(f"Created {db.query(RoomRate).count()} room rates")
        
        # Seed flights (airports, carriers, flights)
        print("Creating sample flights...")
        def get_or_create_airport(code: str, **kwargs) -> Airport:
            a = db.query(Airport).filter(Airport.code == code).first()
            if a:
                return a
            a = Airport(code=code, **kwargs)
            db.add(a)
            db.commit()
            db.refresh(a)
            return a

        jfk = get_or_create_airport(code="JFK", name="John F. Kennedy International Airport", city="New York", country="United States", latitude=40.6413, longitude=-73.7781)
        lax = get_or_create_airport(code="LAX", name="Los Angeles International Airport", city="Los Angeles", country="United States", latitude=33.9416, longitude=-118.4085)
        sfo = get_or_create_airport(code="SFO", name="San Francisco International Airport", city="San Francisco", country="United States", latitude=37.6213, longitude=-122.3790)

        def get_or_create_carrier(code: str, **kwargs) -> Carrier:
            c = db.query(Carrier).filter(Carrier.code == code).first()
            if c:
                return c
            c = Carrier(code=code, **kwargs)
            db.add(c)
            db.commit()
            db.refresh(c)
            return c

        aa = get_or_create_carrier(code="AA", name="American Airlines")
        ua = get_or_create_carrier(code="UA", name="United Airlines")
        dl = get_or_create_carrier(code="DL", name="Delta Air Lines")

        # Two sample nonstop flights
        from datetime import timedelta as _td
        def get_or_create_flight(flight_number: str, **kwargs) -> Flight:
            f = db.query(Flight).filter(Flight.flight_number == flight_number).first()
            if f:
                return f
            f = Flight(flight_number=flight_number, **kwargs)
            db.add(f)
            db.commit()
            db.refresh(f)
            return f

        flight1 = get_or_create_flight(
            flight_number="AA123",
            carrier_id=aa.id,
            origin_airport_id=jfk.id,
            destination_airport_id=lax.id,
            departure_time=datetime.now() + _td(days=7, hours=9),
            arrival_time=datetime.now() + _td(days=7, hours=15),
            duration_minutes=360,
            is_nonstop=True,
            base_price=300.0,
            currency="USD",
            seats_economy=100,
            seats_business=20,
            seats_first=8,
        )
        flight2 = get_or_create_flight(
            flight_number="UA456",
            carrier_id=ua.id,
            origin_airport_id=jfk.id,
            destination_airport_id=sfo.id,
            departure_time=datetime.now() + _td(days=10, hours=8),
            arrival_time=datetime.now() + _td(days=10, hours=13, minutes=30),
            duration_minutes=330,
            is_nonstop=True,
            base_price=280.0,
            currency="USD",
            seats_economy=120,
            seats_business=18,
            seats_first=6,
        )

        # Seed car rentals (vendors, locations, cars)
        print("Creating sample car rentals...")
        def get_or_create_vendor(code: str, **kwargs) -> CarVendor:
            v = db.query(CarVendor).filter(CarVendor.code == code).first()
            if v:
                return v
            v = CarVendor(code=code, **kwargs)
            db.add(v)
            db.commit()
            db.refresh(v)
            return v

        def get_or_create_location(city: str, airport_code: str | None, **kwargs) -> CarLocation:
            q = db.query(CarLocation).filter(CarLocation.city == city)
            if airport_code:
                q = q.filter(CarLocation.airport_code == airport_code)
            l = q.first()
            if l:
                return l
            l = CarLocation(city=city, airport_code=airport_code, **kwargs)
            db.add(l)
            db.commit()
            db.refresh(l)
            return l

        vendor = get_or_create_vendor(name="CityCars", code="CCAR")
        miami_loc = get_or_create_location(city="Miami", airport_code="MIA", country="United States", address="2100 NW 42nd Ave", latitude=25.7959, longitude=-80.2870)
        nyc_loc = get_or_create_location(city="New York", airport_code="JFK", country="United States", address="JFK Airport", latitude=40.6413, longitude=-73.7781)

        def get_or_create_car(location_id: int, make: str, model: str, **kwargs) -> Car:
            c = db.query(Car).filter(Car.location_id == location_id, Car.make == make, Car.model == model).first()
            if c:
                return c
            c = Car(location_id=location_id, make=make, model=model, **kwargs)
            db.add(c)
            db.commit()
            db.refresh(c)
            return c

        get_or_create_car(
            location_id=miami_loc.id,
            vendor_id=vendor.id,
            make="Toyota",
            model="RAV4",
            car_class="suv",
            seats=5,
            doors=4,
            transmission="automatic",
            air_conditioning=True,
            base_price_per_day=55.0,
            currency="USD",
            available_quantity=5,
        )
        get_or_create_car(
            location_id=nyc_loc.id,
            vendor_id=vendor.id,
            make="Honda",
            model="Civic",
            car_class="compact",
            seats=5,
            doors=4,
            transmission="automatic",
            air_conditioning=True,
            base_price_per_day=45.0,
            currency="USD",
            available_quantity=3,
        )
        
        print(f"Created {db.query(Airport).count()} airports")
        print(f"Created {db.query(Carrier).count()} carriers")
        print(f"Created {db.query(Flight).count()} flights")
        print(f"Created {db.query(CarLocation).count()} car locations")
        print(f"Created {db.query(Car).count()} cars")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding database with sample data...")
    seed_database()
    print("Done!") 