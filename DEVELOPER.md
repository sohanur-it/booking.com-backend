# Developer Guide – Backend

This guide explains how to run the backend, change models, create migrations, and seed data.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
uvicorn src.api.main:app --reload
```

## Run with Docker

```bash
docker compose up --build
```

Env vars (compose):
- `DATABASE_URL` – default `sqlite:///./booking_clone.db`
- `SEED_DATA` – set to `true` to run seeds at start

## Models -> Migrations workflow

1) Edit SQLAlchemy models under `src/api/models/*`.
2) Generate migration:

```bash
python manage.py create "Your change"
```

3) Review migration file under `alembic/versions/`.
4) Apply migrations:

```bash
python manage.py migrate
```

Troubleshooting:
- If you see dependency cycles, ensure `branch_labels=None` and `depends_on=None` in generated migration headers, and correct `down_revision` chaining.

## Seeding data

Preferred approach: JSON-driven seeding.

1) Put JSON files in `src/api/seed_json/` (examples already added).
2) Run:

```bash
python manage.py seed
```

The loader is idempotent and supports:
- facility_codes.json, users.json, properties.json (with rooms), rooms.json, bookings.json, reviews.json, payment_methods.json, airports.json, carriers.json, flights.json, car_vendors.json, car_locations.json, cars.json

Fallback: If JSON dir is empty, a demo dataset is inserted programmatically.

### How seeding works (and the small "hack")

- `python manage.py seed` calls `manage_migrations.seed_data()` which imports `src/api/seed_data.py` and runs `seed_database()`.
- `seed_database()` first tries `seed_from_json()` and returns immediately if JSON seeding succeeds. Only if JSON seeding raises an exception will it fall back to programmatic sample data.
- Practically, this means: as long as `src/api/seed_json/` exists and is readable, JSON controls what goes into the DB.

### Adding new data via JSON

Put or edit files under `src/api/seed_json/` and re-run `python manage.py seed`.

- `properties.json` can include nested `rooms` and per-room `rates` (for `room_rates`). Example:

```json
[
  {
    "name": "The Grand Plaza Hotel",
    "address": "123 Main Street",
    "city": "New York",
    "country": "United States",
    "rooms": [
      {
        "name": "Deluxe King Room",
        "base_price": 300.0,
        "rates": [
          {
            "name": "Non-refundable",
            "price": 280.0,
            "currency": "USD",
            "free_cancellation": false,
            "refundable_until": null,
            "pay_at_property": false
          },
          {
            "name": "Breakfast included",
            "price": 320.0,
            "currency": "USD",
            "includes_breakfast": true,
            "free_cancellation": true,
            "refundable_until": "2025-12-01T12:00:00",
            "pay_at_property": true
          }
        ]
      }
    ]
  }
]
```

- `rooms.json` (optional) supports the same `rates` array per room when you seed rooms independently of properties. Include a `property_name` to link the room to a property.

### Idempotency (how duplicates are avoided)

Records are only inserted if a matching row does not already exist, using these keys:
- **FacilityCode**: `code`
- **User**: `email`
- **Property**: `name`
- **Room**: `(property_id, name)`
- **RoomRate**: `(room_id, name)`
- **Booking**: `booking_reference`
- **Review**: `(booking_id, user_id)`
- **PaymentMethod**: `(user_id, last_four_digits)`
- **Airport**: `code`
- **Carrier**: `code`
- **Flight**: `flight_number`
- **CarVendor**: `code`
- **CarLocation**: `(city, airport_code)`
- **Car**: `(location_id, make, model)`

Notes:
- The seeder currently INSERTS new rows; it does not update existing rows. To change seeded data, update it directly in the DB or delete the conflicting rows before re-seeding.
- To force the programmatic sample data instead of JSON, temporarily rename or remove the `src/api/seed_json` directory when running `python manage.py seed`.

### Commands and verification

Using `uv` environment:

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed
```

Quick checks with SQLite:

```bash
sqlite3 booking_clone.db 'SELECT count(*) FROM properties;'
sqlite3 booking_clone.db 'SELECT count(*) FROM rooms;'
sqlite3 booking_clone.db 'SELECT count(*) FROM room_rates;'
```

## Included SQLite database

`booking_clone.db` is committed for convenience. You can:
- Use it as-is (`DATABASE_URL=sqlite:///./booking_clone.db`)
- Replace it with a fresh one by deleting the file and re-running migrations and seed

## Formatting & linting

```bash
ruff check --fix .
autopep8 -r --in-place src
```


