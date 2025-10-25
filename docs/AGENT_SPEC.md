# Agent Implementation Spec — Railway Booking Backend

Purpose: deliver a detailed, actionable specification an implementation agent can follow to implement the FastAPI backend that reads and modifies the existing `database/railway.db` (SQLite).

Location of assets (already in repo):
- `database/railway.db` — SQLite database file with static data preloaded (stations, trains, routes).
- `database/schema.sql` — canonical schema. Use for reference or to reinitialize if needed.
- `data/*.json` — raw data (trains.json, stations.json, schedules.json) for import scripts.

Deliverables expected from agent:
- `backend/` FastAPI app with routes specified below.
- `scripts/` with `init_db.py` and `import_data.py` (idempotent). `init_db.py` should seed admin from env.
- `backend/app/db_utils.py` with reusable DB helper functions.
- Unit tests for booking transactions and seat-hold concurrency.

---

## High-level requirements
- Use existing `database/railway.db` as source of truth.
- All DB writes must go through the backend; frontend only uses API.
- Authentication: JWT tokens via `/api/auth/*` endpoints. Admin role expressed via `users.is_admin`.
- Booking flow: seat hold (TTL) -> booking with mock payment -> transactional booking commit.
- Admin can CRUD trains/stations and run imports.

---

## API Endpoints (detailed)

General notes:
- Base path: `/api`
- Content-Type: `application/json`
- Use standard HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 500 Server Error.

1) Auth
- POST /api/auth/register
  - Purpose: create a normal user (not admin).
  - Body JSON: {"email": "...", "password": "...", "full_name": "...", "phone": "..." }
  - Validation: email format, password length >= 8.
  - Response 201: {"user": {"id","email","full_name"}, "token": "<JWT>"}

- POST /api/auth/login
  - Body JSON: {"email": "...", "password": "..."}
  - Response 200: {"token": "<JWT>", "user": {"id","email","full_name","is_admin"}}

- GET /api/auth/me
  - Auth required (Bearer <token>)
  - Response 200: {user details}

2) Stations
- GET /api/stations?q=term
  - Returns matching stations for autocomplete.
  - Response: [{"code","name","state","zone","latitude","longitude"}, ...]

- GET /api/stations/{code}
  - Response: station record with details.

3) Train search & details
- GET /api/trains/search?from=CODE&to=CODE&date=YYYY-MM-DD
  - Response: array of trains or train_runs matching criteria.
  - Example item:
    {
      "train_number": "12345",
      "train_name": "Example Express",
      "train_id": 12,
      "train_run_id": 123,
      "departure_time": "08:00",
      "arrival_time": "14:00",
      "duration": "6:00",
      "available_classes": ["SLEEPER","3A"],
      "distance_km": 600
    }

- GET /api/trains/{number}?date=YYYY-MM-DD
  - Response: full train info, route (stops), schedule for the run date.

4) Train run availability
- GET /api/train_runs/{run_id}/availability
  - Response: { "train_run_id": ..., "run_date": "...", "seat_summary": [ {"seat_class","total","available","price_cents"}, ... ] }
  - Optional: paginated `seats` list with seat_id, seat_number, coach, class, price, status.

5) Seat holds (short TTL)
- POST /api/seat_holds
  - Auth required.
  - Body JSON: {"train_run_id": 123, "seat_ids": [1,2,3], "hold_seconds": 120}
  - Behavior: create a `seat_holds` entry (or mark `seats.status='HELD'` with hold_owner, hold_expires_at). Return hold token and expires_at.
  - Response 201: {"hold_id": 345, "hold_token": "<uuid>", "expires_at": "..."}
  - Error 409 if seat not available.

- DELETE /api/seat_holds/{hold_id}
  - Cancel/release a hold.

6) Bookings
- POST /api/bookings
  - Auth required.
  - Body JSON:
    {
      "hold_id": 345,                 // OR list of seat_ids + confirmation details
      "train_run_id": 123,
      "from_station_code": "NDLS",
      "to_station_code": "BCT",
      "journey_date": "2025-11-01",
      "passengers": [ {"name":"A","age":30,"gender":"M"}, ... ],
      "payment_method": "mock"
    }
  - Flow: verify hold, perform mock payment, on success run DB transaction to update seats and insert booking rows.
  - Response 201: {"booking_id": "PNR-2025-0001", "status": "CONFIRMED", "total_cents": 150000 }
  - On payment failure return 402/400 with message and release holds.

- GET /api/bookings (auth)
  - Response: list of user's bookings with brief info.

- GET /api/bookings/{booking_id} (auth)
  - Response: full booking details including `booking_seats`.

- POST /api/bookings/{booking_id}/cancel (auth)
  - Behavior: if within cancel policy, set `bookings.status='CANCELLED'` and update seat statuses to `AVAILABLE`. Optionally refund (mock).

7) Admin endpoints (admin-only)
- POST /api/admin/import
  - Body: {"source":"local","force":false}
  - Behavior: run importer for `data/*.json`, insert missing stations, trains, routes, and train_runs/seats. Log results to `import_logs`.

- CRUD: /api/admin/trains, /api/admin/stations, /api/admin/train_runs (standard REST endpoints) — Protect via `is_admin`.

---

## SQL Statements & Transaction Patterns (SQLite)

Important SQLite notes:
- Concurrency: SQLite allows concurrent readers but a single writer. To ensure consistency for booking transactions, use `BEGIN IMMEDIATE` which acquires a reserved lock and prevents other writers.
- Avoid `SELECT ... FOR UPDATE` (not supported). Instead verify rows inside the transaction and then update.

1) Check seat availability (within transaction)

BEGIN IMMEDIATE;
-- Read seat rows and ensure they are AVAILABLE or HELD by this hold
SELECT id, seat_number, status FROM seats
WHERE train_run_id = :train_run_id
  AND id IN (:seat_ids);

-- Verify statuses in application logic. If any not valid -> ROLLBACK and return 409.

2) Update seats to BOOKED and insert booking atomically

-- Example (use parameterized values)
UPDATE seats
SET status = 'BOOKED'
WHERE train_run_id = :train_run_id
  AND id IN (:seat_ids)
  AND (status = 'AVAILABLE' OR (status = 'HELD' AND hold_id = :hold_id));

INSERT INTO bookings (booking_id, user_id, train_run_id, from_station_code, to_station_code, journey_date, total_cents, num_passengers, status, payment_status, booking_time)
VALUES (:booking_id, :user_id, :train_run_id, :from_code, :to_code, :journey_date, :total_cents, :num_passengers, 'CONFIRMED', 'PAID', CURRENT_TIMESTAMP);

-- get booking db id
-- For each seat, insert booking_seats
INSERT INTO booking_seats (booking_id, seat_id, passenger_name, passenger_age, passenger_gender, price_cents)
VALUES (:booking_db_id, :seat_id, :name, :age, :gender, :price_cents);

COMMIT;

3) Release holds (if using seat_holds table)
UPDATE seat_holds SET status='EXPIRED' WHERE id = :hold_id;

4) Cancel booking (atomic)
BEGIN IMMEDIATE;
UPDATE bookings SET status='CANCELLED', cancellation_time = CURRENT_TIMESTAMP WHERE booking_id = :booking_id AND status = 'CONFIRMED';
-- Free seats
UPDATE seats SET status='AVAILABLE' WHERE id IN (
  SELECT seat_id FROM booking_seats WHERE booking_id = (SELECT id FROM bookings WHERE booking_id = :booking_id)
);
COMMIT;

---

## CLI Commands and Scripts (what to implement)

Scripts directory: `scripts/`

1) `scripts/init_db.py`
- Purpose: ensure `database/railway.db` exists, optionally run `database/schema.sql`, and seed admin user.
- Input: env vars `DB_PATH`, `SCHEMA_PATH`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_FULL_NAME`.
- Flags: `--init-schema` to run schema file; `--force` to update admin credentials if already present (do not delete related bookings).
- Exit codes: 0 success, non-zero on failure.

Example PowerShell:
```powershell
$env:ADMIN_EMAIL='admin@example.com'; $env:ADMIN_PASSWORD='StrongPass123!'
python .\scripts\init_db.py --init-schema
```

2) `scripts/import_data.py`
- Purpose: idempotently import `data/stations.json`, `data/trains.json`, `data/schedules.json` into DB.
- Behavior: import stations first, then trains, then train_stops/routes, log into `import_logs` with success/warnings.
- Flags: `--force` to reimport and overwrite metadata; `--skip-seats` to skip generating `train_runs`/`seats`.

3) `scripts/seed_admin.py` (alternative small utility)
- Simple utility to create/update admin using env vars.

4) `scripts/db_inspect.ps1` (optional)
- PowerShell script to show counts: stations, trains, train_runs, seats, bookings, users.

Example PowerShell one-liners
```powershell
# count rows
sqlite3 database/railway.db "SELECT 'stations', COUNT(*) FROM stations;"
sqlite3 database/railway.db "SELECT 'bookings', COUNT(*) FROM bookings;"
```

---

## DB helper functions (backend/app/db_utils.py)
Provide these helper primitives for the agent to implement and reuse across endpoints:
- get_db_connection(db_path) -> sqlite3.Connection (enable row_factory to return dict-like objects)
- create_user(email, password_hash, full_name, phone, is_admin=False)
- get_user_by_email(email)
- verify_and_acquire_seat_hold(train_run_id, seat_ids, user_id, hold_seconds) -> hold_id or error
- release_seat_hold(hold_id)
- finalize_booking_from_hold(hold_id, user_id, booking_payload) -> booking_id or error
- get_train_runs_between(from_code, to_code, date) -> list
- get_availability_for_run(run_id) -> seat_summary and seat list (paginated)

Implementation notes:
- Use transactions for finalize_booking_from_hold; use `BEGIN IMMEDIATE` when performing writes.
- Protect DB access concurrency by using a single connection per request or a connection pool (sqlite3 supports multiple connections but avoid long-lived write locks).

---

## Testing & Validation (must be included by agent)
- Unit tests for user registration/login and JWT issuance.
- Integration tests for booking flow:
  - Test success path: hold -> booking -> DB updates reflect seats booked and booking rows inserted.
  - Test failure: concurrent booking attempts for same seats; ensure only one succeeds and others fail cleanly.
  - Test cancellation: booking cancellation sets booking.status and frees seats.
- Include tests that simulate payment failure to ensure holds are released.

---

## Logging and Observability
- Log imports into `import_logs` table.
- Log booking attempts and outcomes (success/failure) with timestamps and user id.
- Admin routes should log who performed changes.

---

## Security considerations
- Store `JWT_SECRET` in environment; never commit to repo.
- Hash passwords using `passlib[bcrypt]` or Argon2.
- Rate-limit endpoints like `/api/auth/login` and `/api/seat_holds` to mitigate abuse.

---

## Hand-off checklist for agent implementer
- [ ] Create `backend/` directory and set up FastAPI app skeleton.
- [ ] Implement `backend/app/db_utils.py` primitives.
- [ ] Implement auth endpoints (register/login/me) with JWT.
- [ ] Implement seat-hold endpoints and `seat_holds` persistence (or mark `seats` with hold info).
- [ ] Implement booking endpoint with transactional commit (mock payment integration).
- [ ] Implement import script and admin endpoints.
- [ ] Add tests and basic CI (optional local test runner).
- [ ] Provide README updates and usage instructions for running locally.

---

## Estimated implementation time (for planning)
- Backend skeleton + auth: 8 hours
- DB helper functions + import scripts: 8 hours
- Booking flow, seat-hold, and mock payments: 12 hours (includes tests for concurrency)
- Admin endpoints + import UI: 6 hours
- Total: ~34 hours (rough estimate)

---

If you'd like, I will now:
- (A) Add this spec file to the repo (done), and
- (B) scaffold `backend/app/db_utils.py` and `scripts/init_db.py` using the earlier drafted content so the implementer can run basic operations.

Choose next step: scaffold code (db_utils + init_db) OR generate additional test scripts and sample cURL commands for the spec.  
