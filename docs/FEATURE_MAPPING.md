# Feature Mapping — Requested Features vs Current Plan/Spec

This document maps the user's requested features to the existing planning artifacts in the repo (`docs/IMPLEMENTATION_PLAN.md`, `docs/AGENT_SPEC.md`, `backend/README.md`, `database/schema.sql`, `database/BOOKING_FLOW.md`). It shows which parts are covered, where they live, and what remains to implement.

Requested features (from user):
1. User Registration & Login
2. Train Listing
3. Search Trains
4. Seat Reservation / Booking
5. Ticket Details / Confirmation
6. Booking History
7. Admin Panel (Optional)
8. Basic Frontend Features (UI)

Summary status:
- Covered in spec / planned: All requested features are covered in the spec and planning docs.
- Implementations included: Docs, SQL schema, transaction examples, scripts plan.
- Not yet implemented in code: Backend endpoints, import scripts, frontend pages, and CLI utilities (these are scaffold tasks for implementer).

---

Feature-by-feature mapping

1) User Registration & Login
- Spec coverage:
  - `docs/AGENT_SPEC.md` -> Auth endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`.
  - `backend/README.md` -> Auth: JWT, `JWT_SECRET`, password hashing (passlib[bcrypt]).
- DB artifacts:
  - `database/schema.sql` -> `users` table (id, email, password_hash, full_name, phone, is_admin, is_active, created_at, updated_at).
- Doc references:
  - `docs/IMPLEMENTATION_PLAN.md` -> Authentication details and JWT usage.
- Status: Planned and specified. Implementation required: FastAPI auth endpoints and password hashing.

2) Train Listing
- Spec coverage:
  - `docs/AGENT_SPEC.md` -> Train search & details endpoints (`GET /api/trains/search`, `GET /api/trains/{number}`).
- DB artifacts:
  - `database/schema.sql` -> `trains`, `train_routes`, `train_stops`, `train_runs`, `seats`.
- Frontend mapping:
  - `frontend/README.md` -> pages `/` and `/search`, `/train/[number]`.
- Status: Planned and specified. Implementation required: endpoints and frontend list UI.

3) Search Trains
- Spec coverage:
  - `docs/AGENT_SPEC.md` -> Search endpoint `GET /api/trains/search?from=CODE&to=CODE&date=YYYY-MM-DD` and multi-hop note.
- SQL queries reference:
  - `database/queries.sql` contains example search queries and CTE for checking stop sequence.
- Status: Planned and specified. Implementation required: search logic in backend.

4) Seat Reservation / Booking
- Spec coverage:
  - `docs/AGENT_SPEC.md` -> Seat holds (`POST /api/seat_holds`) and `POST /api/bookings`.
  - `database/BOOKING_FLOW.md` -> Transactional booking example, seat hold schema, TTL, mock payment.
  - `backend/README.md` -> Booking & Payment section.
- DB artifacts:
  - `database/schema.sql` -> `train_runs`, `seats`, `bookings`, `booking_seats`.
- Status: Fully specified with transaction examples. Implementation required: seat-hold and booking endpoints, and mock payment service.

5) Ticket Details / Confirmation
- Spec coverage:
  - `docs/AGENT_SPEC.md` -> `GET /api/bookings/{booking_id}` returns booking details and passenger seats.
  - `database/queries.sql` -> `Get booking details with passengers` sample query.
- Frontend mapping:
  - `frontend/README.md` -> `/booking/[booking_id]` page.
- Status: Planned and specified. Implementation required: booking details endpoint and frontend confirmation page.

6) Booking History
- Spec coverage:
  - `docs/AGENT_SPEC.md` -> `GET /api/bookings` for user booking list; `database/queries.sql` -> `Get user's booking history` query.
- DB artifacts:
  - `bookings` and `booking_seats` tables in `database/schema.sql`.
- Status: Planned and specified. Implementation required: endpoint and frontend `/account` page.

7) Admin Panel (Optional)
- Spec coverage:
  - `docs/AGENT_SPEC.md` -> Admin endpoints `POST /api/admin/import`, and CRUD endpoints for trains/stations/runs.
  - `backend/README.md` -> Admin notes and seeding via env (`ADMIN_EMAIL`, `ADMIN_PASSWORD`).
- DB artifacts:
  - `import_logs` and `mapping_warnings` tables in `database/schema.sql`.
- Status: Planned and specified. Implementation required: admin endpoints and optional admin UI.

8) Basic Frontend Features (UI)
- Spec coverage:
  - `frontend/README.md` -> pages list, Tailwind usage, animation libs (GSAP, Framer Motion).
- Status: Planned. Implementation required: Next.js app with Tailwind, components, seat map UI.

---

Gaps & recommended next steps (actionable)

Gaps (currently not implemented in code):
- Backend: No code for FastAPI endpoints, DB helpers, or services yet; only docs/spec exist.
- Scripts: `scripts/init_db.py` and `scripts/import_data.py` are planned but not added to the repo (init_db was drafted previously but not created as file).
- Frontend: No Next.js project files exist; only README planning.
- Tests: Unit/integration tests are not present yet.

Prioritized next steps for implementation agent:
1. Add `backend/app/db_utils.py` with connection helpers and core DB functions (get_user_by_email, create_user, hold seats, finalize booking transaction).
2. Add `scripts/init_db.py` to seed admin and optionally initialize schema (we have earlier draft ready to add).
3. Scaffold FastAPI with auth routes, seat_holds, bookings, and admin import routes wired to `db_utils`.
4. Implement `scripts/import_data.py` to idempotently import `data/*.json` into the DB (stations, trains, stops, runs, seats).
5. Scaffold Next.js frontend with key pages and connect to backend API.
6. Write tests for booking concurrency and seat locking.

Quick developer commands
- Inspect DB counts (PowerShell):
  ```powershell
  sqlite3 database/railway.db "SELECT 'stations', COUNT(*) FROM stations;"
  sqlite3 database/railway.db "SELECT 'trains', COUNT(*) FROM trains;"
  sqlite3 database/railway.db "SELECT 'bookings', COUNT(*) FROM bookings;"
  ```

- Run init script (when added):
  ```powershell
  $env:ADMIN_EMAIL='admin@example.com'; $env:ADMIN_PASSWORD='StrongPass123!'
  python .\scripts\init_db.py --init-schema
  ```

Files to hand to implementation agent
- `docs/AGENT_SPEC.md` (already in repo)
- `docs/IMPLEMENTATION_PLAN.md`
- `database/schema.sql`, `database/queries.sql`, `database/BOOKING_FLOW.md`

---

Status: Ready for implementation
- The planning/specification phase is complete and comprehensive. An implementation agent can now scaffold the backend and frontend using the docs.

If you want, I can now:
- (A) Add the drafted `scripts/init_db.py` to `scripts/` and `backend/app/db_utils.py` helper (minimal working versions), or
- (B) Scaffold FastAPI route stubs wired to those helpers for auth, seat_holds, bookings, and admin.

Pick A or B (or both) and I will proceed to create the files and run basic checks.
