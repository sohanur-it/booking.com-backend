#!/bin/sh
set -e

# Apply migrations
python manage_migrations.py migrate || true

# Optionally seed data
if [ "$SEED_DATA" = "true" ]; then
  echo "Seeding database with sample data..."
  python manage_migrations.py seed || true
fi

# Start API
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000


