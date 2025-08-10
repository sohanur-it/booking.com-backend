from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - SQLite for development
DATABASE_URL = "sqlite:///./booking_clone.db"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Import all models to ensure they are registered with Base
from .models.user import User
from .models.property import Property, Room
from .models.booking import Booking, PaymentMethod
from .models.review import Review, ReviewResponse
from .models.flight import Airport, Carrier, Flight, FlightBooking
from .models.car_rental import CarVendor, CarLocation, Car, CarBooking
from .models.metadata import FacilityCode
# Cart models removed (stateless flow)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

# Drop all tables (for testing)
def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)

# Check if tables exist
def check_tables_exist():
    """Check if database tables exist."""
    try:
        # Try to query the users table
        db = SessionLocal()
        db.execute("SELECT 1 FROM users LIMIT 1")
        db.close()
        return True
    except Exception:
        return False

def get_tax_rates():
    tax_rate = float(os.environ.get('TAX_RATE', 0.1475))
    city_tax = float(os.environ.get('CITY_TAX', 0.04285))
    return tax_rate, city_tax 