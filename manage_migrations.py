#!/usr/bin/env python3
"""
Migration management script for Booking.com clone backend.
This script provides easy commands for managing Alembic migrations.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"🔄 {description}...")
    
    try:
        # Use the virtual environment's Python and Alembic
        venv_python = os.path.join(os.getcwd(), ".venv", "bin", "python")
        venv_alembic = os.path.join(os.getcwd(), ".venv", "bin", "alembic")
        
        # Replace 'uv run alembic' with the direct path
        if command.startswith("uv run alembic"):
            command = command.replace("uv run alembic", venv_alembic)
        
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        print(f"✅ {description or 'Command'} completed successfully!")
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or 'Command'} failed!")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return None

def init_alembic():
    """Initialize Alembic for the project."""
    print("🚀 Initializing Alembic...")
    
    # Check if alembic.ini exists
    if not os.path.exists("alembic.ini"):
        print("❌ alembic.ini not found. Please run this script from the backend directory.")
        return False
    
    # Initialize alembic
    result = run_command("uv run alembic init alembic", "Initializing Alembic")
    if not result:
        return False
    
    print("✅ Alembic initialized successfully!")
    return True

def create_migration(message):
    """Create a new migration."""
    if not message:
        message = input("Enter migration message: ")
    
    print(f"📝 Creating migration: {message}")
    result = run_command(f"uv run alembic revision --autogenerate -m '{message}'", "Creating migration")
    
    if result:
        print("✅ Migration created successfully!")
        print("📋 Review the generated migration file in alembic/versions/")
        print("🚀 Run 'python manage_migrations.py migrate' to apply the migration")
    else:
        print("❌ Failed to create migration")
    
    return result

def migrate():
    """Apply all pending migrations."""
    print("🚀 Applying migrations...")
    result = run_command("uv run alembic upgrade head", "Applying migrations")
    
    if result:
        print("✅ All migrations applied successfully!")
    else:
        print("❌ Migration failed")
    
    return result

def rollback(revision=None):
    """Rollback migrations."""
    if not revision:
        revision = input("Enter revision to rollback to (or 'head-1' for previous): ")
    
    print(f"🔄 Rolling back to revision: {revision}")
    result = run_command(f"uv run alembic downgrade {revision}", f"Rolling back to {revision}")
    
    if result:
        print("✅ Rollback completed successfully!")
    else:
        print("❌ Rollback failed")
    
    return result

def show_status():
    """Show current migration status."""
    print("📊 Migration Status:")
    result = run_command("uv run alembic current", "Checking current migration")
    
    if result:
        print("\n📋 Migration History:")
        run_command("uv run alembic history", "Showing migration history")

def show_history():
    """Show migration history."""
    print("📋 Migration History:")
    run_command("uv run alembic history", "Showing migration history")

def stamp_head():
    """Stamp the database as up-to-date without running migrations."""
    print("🏷️ Stamping database as up-to-date...")
    result = run_command("uv run alembic stamp head", "Stamping database")
    
    if result:
        print("✅ Database stamped successfully!")
    else:
        print("❌ Stamping failed")
    
    return result

def reset_database():
    """Reset the database (drop all tables and recreate)."""
    print("⚠️ WARNING: This will delete all data!")
    confirm = input("Are you sure you want to reset the database? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Database reset cancelled")
        return False
    
    print("🗑️ Resetting database...")
    
    # Drop all tables
    result = run_command("uv run alembic downgrade base", "Dropping all tables")
    if not result:
        print("❌ Failed to drop tables")
        return False
    
    # Recreate tables
    result = run_command("uv run alembic upgrade head", "Recreating tables")
    if not result:
        print("❌ Failed to recreate tables")
        return False
    
    print("✅ Database reset successfully!")
    return True

def seed_data():
    """Seed the database with sample data."""
    print("🌱 Seeding database with sample data...")
    
    # Start the server temporarily to seed data
    try:
        # Import and run seed function directly
        import sys
        sys.path.append('src')
        from api.seed_data import seed_database
        
        seed_database()
        print("✅ Database seeded successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to seed database: {e}")
        return False

def show_help():
    """Show help information."""
    print("""
🔧 Booking.com Clone - Migration Management

Usage: python manage_migrations.py <command> [options]

Commands:
  init              Initialize Alembic (first time setup)
  create <message>  Create a new migration
  migrate           Apply all pending migrations
  rollback [rev]    Rollback to a specific revision
  status            Show current migration status
  history           Show migration history
  stamp             Stamp database as up-to-date
  reset             Reset database (drop all tables)
  seed              Seed database with sample data
  help              Show this help message

Examples:
  python manage_migrations.py init
  python manage_migrations.py create "Add user table"
  python manage_migrations.py migrate
  python manage_migrations.py rollback head-1
  python manage_migrations.py status
  python manage_migrations.py reset
  python manage_migrations.py seed

Migration Workflow:
1. Make changes to your SQLAlchemy models
2. Run: python manage_migrations.py create "Description of changes"
3. Review the generated migration file
4. Run: python manage_migrations.py migrate
5. Test your application

Rollback Workflow:
1. Run: python manage_migrations.py history
2. Choose the revision to rollback to
3. Run: python manage_migrations.py rollback <revision>
""")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        init_alembic()
    elif command == "create":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        create_migration(message)
    elif command == "migrate":
        migrate()
    elif command == "rollback":
        revision = sys.argv[2] if len(sys.argv) > 2 else None
        rollback(revision)
    elif command == "status":
        show_status()
    elif command == "history":
        show_history()
    elif command == "stamp":
        stamp_head()
    elif command == "reset":
        reset_database()
    elif command == "seed":
        seed_data()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main() 