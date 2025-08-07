"""
Database migration script for Booking.com clone backend.
This script handles database schema creation and updates.
"""

import os
import sqlite3
from sqlalchemy import text
from .database import engine, SessionLocal, create_tables, check_tables_exist

def run_migrations():
    """Run all database migrations."""
    print("Starting database migrations...")
    
    # Check if database file exists
    db_file = "./booking_clone.db"
    db_exists = os.path.exists(db_file)
    
    if not db_exists:
        print("Creating new database...")
        create_tables()
        print("✅ Database created successfully!")
        return True
    
    # Check if tables exist
    if not check_tables_exist():
        print("Database exists but tables are missing. Creating tables...")
        create_tables()
        print("✅ Tables created successfully!")
        return True
    
    print("✅ Database and tables already exist!")
    return True

def reset_database():
    """Reset the database (drop all tables and recreate)."""
    print("Resetting database...")
    
    # Drop all tables
    from .database import drop_tables
    drop_tables()
    
    # Create tables again
    create_tables()
    
    print("✅ Database reset successfully!")

def check_database_status():
    """Check the current status of the database."""
    print("Checking database status...")
    
    db_file = "./booking_clone.db"
    if not os.path.exists(db_file):
        print("❌ Database file does not exist")
        return False
    
    if not check_tables_exist():
        print("❌ Database exists but tables are missing")
        return False
    
    # Check table structure
    try:
        db = SessionLocal()
        
        # Check if all required tables exist
        tables = ['users', 'properties', 'rooms', 'bookings', 'reviews', 'review_responses', 'payment_methods']
        existing_tables = []
        
        for table in tables:
            try:
                result = db.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"))
                if result.fetchone():
                    existing_tables.append(table)
            except Exception:
                pass
        
        db.close()
        
        missing_tables = set(tables) - set(existing_tables)
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print(f"✅ All tables exist: {existing_tables}")
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

def create_migration_script():
    """Create a SQL migration script for manual execution."""
    print("Creating migration script...")
    
    migration_sql = """
-- Booking.com Clone Database Migration Script
-- Run this script to create all necessary tables

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATETIME,
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    genius_level INTEGER DEFAULT 1,
    total_bookings INTEGER DEFAULT 0,
    total_spent FLOAT DEFAULT 0.0,
    genius_discount_percentage FLOAT DEFAULT 0.0,
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    preferred_language VARCHAR(5) DEFAULT 'en',
    marketing_emails BOOLEAN DEFAULT 1
);

-- Properties table
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    address VARCHAR(500) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    latitude FLOAT,
    longitude FLOAT,
    property_type VARCHAR(50),
    star_rating INTEGER,
    total_rooms INTEGER,
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    amenities TEXT, -- JSON array
    facilities TEXT, -- JSON array
    base_price FLOAT,
    currency VARCHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT 1,
    images TEXT, -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    room_type VARCHAR(100),
    max_guests INTEGER DEFAULT 2,
    size_sqm FLOAT,
    room_amenities TEXT, -- JSON array
    base_price FLOAT NOT NULL,
    genius_price FLOAT,
    total_quantity INTEGER DEFAULT 1,
    available_quantity INTEGER DEFAULT 1,
    images TEXT, -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties (id)
);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_reference VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    check_in_date DATETIME NOT NULL,
    check_out_date DATETIME NOT NULL,
    num_guests INTEGER DEFAULT 1,
    num_rooms INTEGER DEFAULT 1,
    guest_names TEXT, -- JSON array
    special_requests TEXT,
    base_price FLOAT NOT NULL,
    genius_discount FLOAT DEFAULT 0.0,
    taxes FLOAT DEFAULT 0.0,
    total_price FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    free_cancellation BOOLEAN DEFAULT 0,
    cancellation_deadline DATETIME,
    cancellation_fee FLOAT DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'pending',
    payment_status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_details TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confirmed_at DATETIME,
    cancelled_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (room_id) REFERENCES rooms (id)
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    booking_id INTEGER NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    overall_rating FLOAT NOT NULL,
    cleanliness_rating FLOAT,
    comfort_rating FLOAT,
    location_rating FLOAT,
    facilities_rating FLOAT,
    staff_rating FLOAT,
    value_for_money_rating FLOAT,
    wifi_rating FLOAT,
    is_verified_stay BOOLEAN DEFAULT 1,
    helpful_votes INTEGER DEFAULT 0,
    is_helpful BOOLEAN DEFAULT 0,
    is_approved BOOLEAN DEFAULT 1,
    is_flagged BOOLEAN DEFAULT 0,
    moderation_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (property_id) REFERENCES properties (id),
    FOREIGN KEY (booking_id) REFERENCES bookings (id)
);

-- Review responses table
CREATE TABLE IF NOT EXISTS review_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    responder_type VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews (id)
);

-- Payment methods table
CREATE TABLE IF NOT EXISTS payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    method_type VARCHAR(50) NOT NULL,
    card_type VARCHAR(50),
    last_four_digits VARCHAR(4),
    expiry_month INTEGER,
    expiry_year INTEGER,
    cardholder_name VARCHAR(255),
    is_default BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings (user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_room_id ON bookings (room_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings (status);
CREATE INDEX IF NOT EXISTS idx_reviews_property_id ON reviews (property_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews (user_id);
CREATE INDEX IF NOT EXISTS idx_rooms_property_id ON rooms (property_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON payment_methods (user_id);

PRAGMA foreign_keys = ON;
"""
    
    with open("migration.sql", "w") as f:
        f.write(migration_sql)
    
    print("✅ Migration script created: migration.sql")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            run_migrations()
        elif command == "reset":
            reset_database()
        elif command == "status":
            check_database_status()
        elif command == "create-script":
            create_migration_script()
        else:
            print("Unknown command. Available commands: migrate, reset, status, create-script")
    else:
        print("Running migrations...")
        run_migrations() 