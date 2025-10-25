# Backend — FastAPI (planned)

This README describes the planned backend architecture, dependencies, environment variables, and management commands for the FastAPI backend.

## Tech stack
- Python 3.10+ (recommended)
- FastAPI for HTTP API
- SQLModel or SQLAlchemy for ORM
- SQLite as local database (`database/railway.db`)
- passlib[bcrypt] for password hashing
- python-dotenv for local env loading

## Planned dependencies (to add to `backend/requirements.txt`)
```
fastapi
uvicorn[standard]
sqlmodel
passlib[bcrypt]
python-dotenv
PyJWT
```

## Environment variables
- DB_PATH=database/railway.db
- SCHEMA_PATH=database/schema.sql
- JWT_SECRET=replace_with_a_secure_random_secret
- JWT_ALGORITHM=HS256
- JWT_EXPIRES_MINUTES=60
- ADMIN_EMAIL (for initial seed)
- ADMIN_PASSWORD (for initial seed)

Create a `.env` or set environment variables in your development environment.

## Management scripts
- `scripts/init_db.py` — initialize DB and seed admin from environment variables
- `scripts/import_data.py` — import `data/*.json` into DB (stations, trains, schedules)

## Auth
- JWT auth for all protected routes.
- `/api/auth/register` and `/api/auth/login` endpoints.

## Admin
- Admin-only routes for CRUD operations and import control. Protect admin endpoints by verifying `is_admin` in JWT claims.

## Booking & Payment
This project uses a transactional booking flow with a short seat-hold period and mock payments during development.

Planned booking sequence:
- Client requests seat availability and shows seat map.
- Client requests a seat hold (`POST /api/seat_holds`) — backend marks seats `HELD` with a TTL (e.g., 120s).
- Client submits passenger info and requests booking (`POST /api/bookings`). Backend verifies hold, performs mock payment, and on success runs a DB transaction to mark seats `BOOKED`, insert `bookings` and `booking_seats`, and clear holds.
- If payment fails or the hold expires, backend releases held seats and returns an error.

Mock payment:
- Implement a simple mock payment service in `app/services/payments.py` that returns success in development. Make failure deterministic via a configuration flag for testing.

Database updates on confirmed payment:
- Update `seats.status` to `BOOKED` and `updated_at`.
- Insert row in `bookings` and corresponding `booking_seats` rows.
- These operations MUST be executed inside a single database transaction to prevent double-booking.

See `database/BOOKING_FLOW.md` for SQL transaction examples and hold/booking strategies.

## Running locally (after implementation)
```powershell
# from repo root
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Tests
- Add pytest tests for booking transactions, seat locking, and auth flows.

## Notes
- No direct DB edits from frontend — all DB modifications must go through backend endpoints.
- Admin credentials seeded via env; do not print JWTs from init script.
