# Implementation Plan — Railway Booking App

This document captures the detailed plan for implementing the local Railway Booking app (FastAPI backend, Next.js frontend). It is intended as the single-source plan to hand to an implementation agent.

## Summary
- Backend: FastAPI + SQLAlchemy/SQLModel, JWT auth, SQLite (`database/railway.db`)
- Frontend: Next.js (TypeScript recommended) + Tailwind CSS + GSAP/Framer Motion
- Data import: scripts will import `data/trains.json`, `data/stations.json`, and `data/schedules.json` into the DB schema defined in `database/schema.sql`.
- Admin: seeded via env variables during DB init; admin can perform CRUD on trains, stations, runs, and run imports.
- Booking: transactional seat booking with short TTL seat hold; mock payment provider.

---

## File layout (canonical)
- `backend/` — FastAPI app
  - `app/main.py` — FastAPI app entry
  - `app/api/` — routers
  - `app/models/` — SQLAlchemy/SQLModel models & Pydantic schemas
  - `app/core/` — auth, config, utils, JWT handling
  - `app/db/` — DB session, migration helpers
  - `app/services/` — booking logic, seat locking
- `frontend/` — Next.js app
  - `pages/` — top-level pages
  - `components/` — UI pieces
  - `styles/` — Tailwind config, globals
- `scripts/` — `init_db.py`, `import_data.py`
- `database/` — `schema.sql`, `queries.sql`, optional `railway.db`
- `data/` — source JSON files (already present)
- `docs/` — this plan and further docs

---

## API contract (core endpoints)
Note: use JSON responses. Protect necessary routes with JWT.

Auth
- POST /api/auth/register
  - body: { email, password, full_name }
  - response: { user: {id,email,full_name}, token }
- POST /api/auth/login
  - body: { email, password }
  - response: { token, user }

Stations
- GET /api/stations?q=term
  - response: [{ code, name, latitude, longitude, state, zone }]

Trains & Search
- GET /api/trains/search?from=CODE&to=CODE&date=YYYY-MM-DD
  - response: [{ number, name, departure_time, arrival_time, duration, classes, train_run_id }]
- GET /api/trains/{number}?date=YYYY-MM-DD
  - response: train details + route stops

Availability
- GET /api/train_runs/{run_id}/availability
  - response: seat summary and optionally paginated seat list

Bookings
- POST /api/bookings (auth)
  - body: { train_run_id, from_station, to_station, journey_date, seats: [seat_id], passengers: [{name,age,gender}] }
  - response: { booking_id, status, seats_assigned }
- GET /api/bookings (auth)
  - response: list of user's bookings
- GET /api/bookings/{booking_id} (auth)
  - response: booking details
- POST /api/bookings/{booking_id}/cancel (auth)
  - response: cancellation confirmation

Admin
- POST /api/admin/import (admin)
  - body: { source: 'local', force: bool }
  - response: import summary
- CRUD endpoints for trains/stations/runs protected with admin check

---

## DB schema summary (from `database/schema.sql`)
Key tables:
- users(id, email, password_hash, full_name, phone, is_admin, is_active, created_at, updated_at)
- trains (id, number, name, type, from_station_code, to_station_code, departure_time, arrival_time, duration)
- stations(code, name, state, latitude, longitude, zone, address)
- train_stops (train_id, stop_sequence, station_code, arrival_time, departure_time, day_offset)
- train_runs (id, train_id, run_date, total_seats, available_seats)
- seats (id, train_run_id, seat_number, coach_number, seat_class, price_cents, status)
- bookings (id, booking_id, user_id, train_run_id, from_station_code, to_station_code, journey_date, total_cents, num_passengers, status, booking_time)
- booking_seats (id, booking_id, seat_id, passenger_name, passenger_age, passenger_gender, price_cents)

Refer to `database/schema.sql` for exact column types and constraints.

---

## Seat locking and booking flow (design)
1. User requests availability -> client shows seat map.
2. When user selects seats, client calls POST /api/seat_holds to create a temporary hold (TTL ~120s).
3. Backend checks seats are `AVAILABLE` and inserts a `seat_hold` row (or uses `seats.status='HELD'` with hold_owner and expire_at) inside transaction.
4. Client completes passenger details and calls POST /api/bookings -> backend verifies hold, updates seats to `BOOKED`, creates `bookings` and `booking_seats`, calls mock payment provider, commits transaction.
5. If payment fails or TTL expires, backend releases holds.

### Booking payment and DB updates (explicit)

Flow on booking confirmation:

- Verify hold validity and seat ownership (hold not expired).
- Run mock payment (synchronous for initial implementation).
- If payment succeeds:
  - Begin DB transaction.
  - Update `seats` rows to `BOOKED` for the selected seats.
  - Insert a `bookings` row with `booking_id`, `user_id`, `train_run_id`, `from_station_code`, `to_station_code`, `journey_date`, `total_cents`, `num_passengers`, `status='CONFIRMED'`.
  - Insert `booking_seats` rows for each passenger/seat.
  - Commit transaction.
- If payment fails: rollback and release holds.

Sample SQL (from `database/queries.sql` and `database/BOOKING_FLOW.md`) provides a full transaction template. Ensure all seat-checks and updates occur within the same transaction to avoid race conditions.

Mock payment service notes:
- Implement `app/services/payments/mock.py` returning success by default.
- Add a config flag `PAYMENT_FAIL_RATE` for testing failure cases.
- Logging: record payment attempts and outcomes for debugging and analytics.

---

## Admin seeding & init
- `scripts/init_db.py` will initialize DB from `database/schema.sql` (optional) and seed an admin user using `ADMIN_EMAIL` and `ADMIN_PASSWORD` environment variables.
- The admin seed will NOT delete bookings/relations. `--force` will only update the admin credentials and flags.

---

## Import pipeline
- `scripts/import_data.py` reads `data/*.json` and maps to DB tables.
- Steps: stations -> trains -> train_stops/schedules -> train_runs & seats.
- Implement idempotent import with `import_logs` to resume or skip already-imported items.

---

## Security & validation
- Passwords hashed with bcrypt (via Passlib).
- JWT tokens for auth; secret set via `JWT_SECRET` env var.
- Validate email format and password length (>=8) on registration.
- Sanity checks on booking requests: seat ids must belong to same `train_run_id` and be `AVAILABLE`.

---

## Timeline estimates (rough)
- Backend skeleton & auth: 8–12 hours
- Importer & DB wiring: 6–10 hours
- Booking & seat locking: 6–10 hours
- Frontend basic pages: 10–16 hours
- Admin UI & polish: 4–8 hours

---

## Next actions for implementation agent
1. Create repository scaffolding per file layout.
2. Implement `scripts/init_db.py` and `scripts/import_data.py`.
3. Build FastAPI app with endpoints above; include unit tests for booking transaction.
4. Build minimal Next.js UI to exercise booking flow.

---

This document is ready to be used by the implementation agent. When you are ready I can generate the initial code scaffolding and add the `scripts/init_db.py` script content into the repository.
