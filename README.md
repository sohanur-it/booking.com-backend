# Booking.com Clone – Backend (FastAPI)

Production-like backend for a Booking.com-style app. Includes stays, flights, car rentals, reviews, Genius loyalty, and JSON-driven seeding.

## Quick start with Docker

1) Create a `.env` (optional) or use defaults from compose

2) Build and run

```bash
docker compose up --build
```

The API will be available at http://localhost:8000 with docs at http://localhost:8000/docs

Environment flags in compose:
- `DATABASE_URL`: Defaults to `sqlite:///./booking_clone.db`
- `SEED_DATA`: "true" to seed on container start (defaults to "false")

## Local development (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .[dev]  # or: pip install -r requirements
uvicorn src.api.main:app --reload
```

## Database & Migrations

This project uses Alembic. Management commands are wrapped in `manage.py`:

```bash
# Create a new migration after model changes
python manage.py create "Describe your change"

# Apply all pending migrations
python manage.py migrate

# Check status / history
python manage.py status
python manage.py history

# Rollback
python manage.py rollback head-1
```

### Seeding data

There are two seeding modes:

1) JSON-driven (recommended): Place JSON files under `src/api/seed_json/` (e.g., `users.json`, `properties.json`, `airports.json`, etc.). Then run:

```bash
python manage.py seed
```

2) Programmatic fallback: If the JSON folder is empty, the script seeds demo data.

You can also provide a custom folder by calling `seed_from_json('/path/to/folder')` in Python.

### Bundled SQLite DB

The repo includes `booking_clone.db` in the backend root so a fresh clone can run immediately without seeding. Set `DATABASE_URL=sqlite:///./booking_clone.db` (default in compose).

## Project structure highlights

- `src/api/__init__.py` – app factory, routers registration
- Routers: `properties.py`, `bookings.py`, `reviews.py`, `flights.py`, `car_rentals.py`, `filters.py`, `metadata.py`, `packages.py`, `activities.py`
- Models: `user.py`, `property.py`, `booking.py`, `review.py`, `flight.py`, `car_rental.py`, `metadata.py`
- Seeding: `seed_data.py` (+ `src/api/seed_json/*`)

## Useful endpoints

- Health: `GET /health`
- Docs: `/docs`, `/redoc`
- Filters metadata: `GET /api/v1/filters/stays|flights|cars`
- Seeding (dev only): `POST /seed-data`

