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

## Included SQLite database

`booking_clone.db` is committed for convenience. You can:
- Use it as-is (`DATABASE_URL=sqlite:///./booking_clone.db`)
- Replace it with a fresh one by deleting the file and re-running migrations and seed

## Formatting & linting

```bash
ruff check --fix .
autopep8 -r --in-place src
```


