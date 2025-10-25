# Railway Booking — Local Full‑Stack App

This repository contains planning materials and data for a local Railway Booking application.

Purpose
- Provide a local, self-contained platform for searching trains, booking seats, and managing bookings.
- Frontend: Next.js + Tailwind CSS, GSAP/Framer Motion for animation polish.
- Backend: FastAPI (Python), JWT auth, SQLite (`database/railway.db`) using the provided schema.

What you’ll find here
- `data/` — source data: `trains.json`, `stations.json`, `schedules.json` (already present).
- `database/` — `schema.sql`, `queries.sql`, and an optional `railway.db` SQLite file.
- `backend/` — FastAPI backend (implementation to be added). See `backend/README.md` for planned details.
- `frontend/` — Next.js frontend (implementation to be added). See `frontend/README.md` for planned details.
- `scripts/` — management scripts (init DB, import data). See `scripts/README.md`.
- `docs/IMPLEMENTATION_PLAN.md` — detailed implementation plan, API contract, and DB summary.

Quick next steps
1. Review `docs/IMPLEMENTATION_PLAN.md` for the detailed API, DB layout, and import strategy.
2. Run the DB init script (planned in `scripts/`) to create and seed an admin user from environment variables.
3. Implement backend FastAPI following `backend/README.md`, then build the Next.js frontend.

Notes
- All development is intended to run locally on `localhost` with no hosting required.
- Credentials for the initial admin user should be provided via environment variables for automation.

See `docs/IMPLEMENTATION_PLAN.md` for the full plan and API contract.
