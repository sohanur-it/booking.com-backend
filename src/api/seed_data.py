"""
Data seeding script for Booking.com clone backend.
Run this script to populate the database with sample data for testing.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from .database import SessionLocal, engine
from .models.user import User
from .models.property import Property, Room
from .models.booking import Booking, BookingStatus, PaymentStatus, PaymentMethod
from .models.review import Review, ReviewResponse
from .auth import get_password_hash

def seed_database():
    """Seed the database with sample data."""
    db = SessionLocal()
    
    try:
        # Create sample users
        print("Creating sample users...")
        
        # Sample user 1
        user1 = User(
            email="john.doe@example.com",
            password_hash=get_password_hash("password123"),
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            is_verified=True,
            genius_level=2,
            total_bookings=7,
            total_spent=2500.0,
            genius_discount_percentage=15.0
        )
        db.add(user1)
        
        # Sample user 2
        user2 = User(
            email="jane.smith@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Jane",
            last_name="Smith",
            phone="+1987654321",
            is_verified=True,
            genius_level=1,
            total_bookings=3,
            total_spent=800.0,
            genius_discount_percentage=10.0
        )
        db.add(user2)
        
        # Sample user 3 (Genius Level 3)
        user3 = User(
            email="mike.johnson@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Mike",
            last_name="Johnson",
            phone="+1555123456",
            is_verified=True,
            genius_level=3,
            total_bookings=20,
            total_spent=7500.0,
            genius_discount_percentage=20.0
        )
        db.add(user3)
        
        db.commit()
        db.refresh(user1)
        db.refresh(user2)
        db.refresh(user3)
        
        # Create sample properties
        print("Creating sample properties...")
        
        # Property 1 - Luxury Hotel
        property1 = Property(
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
            images=[
                "https://example.com/grand-plaza-1.jpg",
                "https://example.com/grand-plaza-2.jpg",
                "https://example.com/grand-plaza-3.jpg"
            ]
        )
        db.add(property1)
        
        # Property 2 - Boutique Hotel
        property2 = Property(
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
        db.add(property2)
        
        # Property 3 - Resort
        property3 = Property(
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
        db.add(property3)
        
        db.commit()
        db.refresh(property1)
        db.refresh(property2)
        db.refresh(property3)
        
        # Create sample rooms
        print("Creating sample rooms...")
        
        # Rooms for Property 1
        room1_1 = Room(
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
        db.add(room1_1)
        
        room1_2 = Room(
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
        db.add(room1_2)
        
        # Rooms for Property 2
        room2_1 = Room(
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
        db.add(room2_1)
        
        # Rooms for Property 3
        room3_1 = Room(
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
        db.add(room3_1)
        
        db.commit()
        db.refresh(room1_1)
        db.refresh(room1_2)
        db.refresh(room2_1)
        db.refresh(room3_1)
        
        # Create sample bookings
        print("Creating sample bookings...")
        
        # Past booking for user1
        booking1 = Booking(
            booking_reference="BK-20241201-ABC12",
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
            confirmed_at=datetime.now() - timedelta(days=35)
        )
        db.add(booking1)
        
        # Current booking for user2
        booking2 = Booking(
            booking_reference="BK-20241201-DEF34",
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
            confirmed_at=datetime.now() - timedelta(days=10)
        )
        db.add(booking2)
        
        db.commit()
        db.refresh(booking1)
        db.refresh(booking2)
        
        # Create sample reviews
        print("Creating sample reviews...")
        
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
            is_approved=True
        )
        db.add(review1)
        
        db.commit()
        db.refresh(review1)
        
        # Create sample payment methods
        print("Creating sample payment methods...")
        
        payment_method1 = PaymentMethod(
            user_id=user1.id,
            method_type="credit_card",
            card_type="visa",
            last_four_digits="1234",
            expiry_month=12,
            expiry_year=2025,
            cardholder_name="John Doe",
            is_default=True,
            is_active=True
        )
        db.add(payment_method1)
        
        payment_method2 = PaymentMethod(
            user_id=user2.id,
            method_type="credit_card",
            card_type="mastercard",
            last_four_digits="5678",
            expiry_month=8,
            expiry_year=2026,
            cardholder_name="Jane Smith",
            is_default=True,
            is_active=True
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