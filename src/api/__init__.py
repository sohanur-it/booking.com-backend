from fastapi import APIRouter, FastAPI
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import and_
from .database import SessionLocal
from .models.booking import Booking, BookingStatus
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import subprocess
import sys
import os

from .database import create_tables, check_tables_exist
from .routers import auth, properties, bookings, reviews
from .routers import flights, car_rentals, filters, metadata, packages, activities
from .seed_data import seed_database

# Initialize database with Alembic
def init_database():
    """Initialize database using Alembic migrations."""
    try:
        # Check if we're in the backend directory
        backend_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        os.chdir(backend_dir)
        
        # Check if alembic is available
        try:
            # Run alembic current to check if migrations are set up
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "current"],
                capture_output=True,
                text=True,
                cwd=backend_dir,
                timeout=30  # Add timeout to prevent hanging
            )
            
            if result.returncode != 0:
                # Initialize alembic if not already done
                print("Initializing Alembic...")
                subprocess.run(
                    [sys.executable, "-m", "alembic", "init", "alembic"],
                    cwd=backend_dir,
                    check=True,
                    timeout=60  # Add timeout to prevent hanging
                )
            
            # Run migrations
            print("Running database migrations...")
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=backend_dir,
                check=True,
                timeout=60  # Add timeout to prevent hanging
            )
            print("✅ Database migrations completed successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Migration failed: {e}")
            # Fallback to manual table creation
            print("Falling back to manual table creation...")
            create_tables()
            print("✅ Manual table creation completed!")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Fallback to manual table creation
        print("Falling back to manual table creation...")
        create_tables()
        print("✅ Manual table creation completed!")

main_router = APIRouter()


@main_router.get("/")
@main_router.head("/")
async def root():
    return {"message": "Welcome to Booking.com Clone API!"}


@main_router.get("/health")
@main_router.head("/health")
async def health_check():
    return {"status": "healthy", "service": "booking-clone-api"}


@main_router.get("/api/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello {name}!"}


@main_router.post("/seed-data")
async def seed_sample_data():
    """Seed the database with sample data for testing."""
    try:
        seed_database()
        return {"message": "Database seeded successfully with sample data!"}
    except Exception as e:
        return {"error": f"Failed to seed database: {str(e)}"}


def create_app():
    # Initialize database when app starts
    init_database()
    
    app = FastAPI(
        title="Booking.com Clone API", 
        version="1.0.0",
        description="A comprehensive Booking.com clone backend API with all core features",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(main_router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(properties.router, prefix="/api/v1")
    app.include_router(bookings.router, prefix="/api/v1")
    app.include_router(reviews.router, prefix="/api/v1")
    app.include_router(flights.router, prefix="/api/v1")
    app.include_router(car_rentals.router, prefix="/api/v1")
    app.include_router(filters.router, prefix="/api/v1")
    app.include_router(metadata.router, prefix="/api/v1")
    app.include_router(packages.router, prefix="/api/v1")
    app.include_router(activities.router, prefix="/api/v1")

    # Background task: expire old pending bookings (runs every minute)
    async def _expire_stale_pending_bookings_loop() -> None:
        while True:
            print("Expiring stale pending bookings...")
            # wait first to avoid load spikes at startup
            await asyncio.sleep(60)
            try:
                default_tz = ZoneInfo("America/New_York")
                now_utc = datetime.now(default_tz).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                print(f"Now UTC: {now_utc}")
                threshold = now_utc - timedelta(minutes=15)
                db = SessionLocal()
                stale = db.query(Booking).filter(
                    and_(
                        Booking.status == BookingStatus.PENDING,
                        Booking.created_at < threshold,
                    )
                ).all()
                print(f"Stale bookings: {stale}")
                if stale:
                    for b in stale:
                        b.status = BookingStatus.CANCELLED
                    db.commit()
            except Exception:
                # Avoid crashing app if background job fails
                pass
            finally:
                try:
                    db.close()
                except Exception:
                    pass

    @app.on_event("startup")
    async def _start_background_tasks() -> None:
        asyncio.create_task(_expire_stale_pending_bookings_loop())

    def custom_openapi():
        """
        Generate custom OpenAPI schema for the Booking.com clone API.
        """
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Booking.com Clone API",
            version="1.0.0",
            summary="Complete Booking.com clone backend API",
            description="""
            # Booking.com Clone API
            
            A comprehensive backend API that replicates all core Booking.com functionality:
            
            ## Features
            
            ### Authentication & User Management
            - User registration and login
            - Password reset functionality
            - JWT token-based authentication
            - User profile management
            
            ### Genius Loyalty Program
            - Track booking count and spending
            - Automatic level progression (Level 1, 2, 3)
            - Discount calculation (10%, 15%, 20%)
            - Next level requirements tracking
            
            ## API Endpoints
            
            ### Authentication
            - `POST /api/v1/auth/register` - User registration
            - `POST /api/v1/auth/login` - User login
            - `POST /api/v1/auth/password-reset-request` - Request password reset
            - `POST /api/v1/auth/password-reset` - Reset password
            - `GET /api/v1/auth/me` - Get current user info
            - `PUT /api/v1/auth/me` - Update user profile
            - `GET /api/v1/auth/genius-info` - Get Genius loyalty info
            
            ### Development
            - `POST /seed-data` - Seed database with sample data
            
            ## Database Schema
            
            The API uses SQLite with the following main tables:
            - `users` - User accounts and Genius loyalty data
            
            ## Authentication
            
            The API uses JWT tokens for authentication. Include the token in the Authorization header:
            ```
            Authorization: Bearer <your-jwt-token>
            ```
            
            ## Genius Loyalty Program
            
            Users automatically progress through Genius levels based on bookings and spending:
            - **Level 1**: 1+ bookings, 10% discount
            - **Level 2**: 5+ bookings, $1000+ spent, 15% discount  
            - **Level 3**: 15+ bookings, $5000+ spent, 20% discount
            
            ## Sample Data
            
            The API includes a `/seed-data` endpoint that populates the database with:
            - 3 sample users (different Genius levels)
            - 3 properties (hotel, boutique, resort)
            - Multiple room types with pricing
            - Sample bookings and reviews
            - Payment methods
            
            ## Database Migrations
            
            This API uses Alembic for automatic database migrations:
            - Automatic schema detection from SQLAlchemy models
            - Version control for database changes
            - Rollback capabilities
            - Migration history tracking
            
            ## Offline Capability
            
            This API is designed to work completely offline with mock data, making it perfect for:
            - Development and testing
            - Offline demonstrations
            - Learning and educational purposes
            """,
            routes=app.routes,
        )
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    return app
