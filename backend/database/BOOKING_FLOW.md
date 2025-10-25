# Booking Flow & Transaction Example

This document describes the recommended backend booking flow, including seat holds, mock payment handling, and the SQL transaction pattern to update `bookings` and `booking_seats` tables.

Goals
- Ensure seat allocation is atomic and consistent.
- Prevent double-booking via seat hold / lock with TTL.
- Update `bookings` and `booking_seats` only after payment confirmation (mocked).

High-level workflow
1. User requests availability and views seat map.
2. User selects seats and submits a hold request: POST /api/seat_holds
   - Backend checks seats are AVAILABLE and creates a `seat_holds` entry (or marks `seats.status='HELD'`) with `hold_owner`, `hold_expires_at`.
   - Hold TTL recommended: 120 seconds.
3. Client completes passenger data and initiates booking: POST /api/bookings
   - Backend verifies the hold belongs to the user and is not expired.
   - Backend initiates mock payment: either synchronous mock success or a simulated delay/failure.
   - On payment success, backend runs a DB transaction to mark seats BOOKED and insert booking records.
   - On payment failure or expiry, backend releases holds and returns error to client.

SQL transaction example (SQLite pseudocode)

BEGIN TRANSACTION;

-- Verify seats are still available (or held by this hold_id)
SELECT id, status FROM seats
WHERE train_run_id = :train_run_id
  AND seat_number IN (:seat_numbers)
  AND (status = 'AVAILABLE' OR (status = 'HELD' AND hold_id = :hold_id));

-- Update seats to BOOKED (only if currently AVAILABLE or HELD by this hold)
UPDATE seats
SET status = 'BOOKED', updated_at = CURRENT_TIMESTAMP
WHERE train_run_id = :train_run_id
  AND seat_number IN (:seat_numbers)
  AND (status = 'AVAILABLE' OR (status = 'HELD' AND hold_id = :hold_id));

-- Insert booking row
INSERT INTO bookings
(booking_id, user_id, train_run_id, from_station_code, to_station_code, journey_date, total_cents, num_passengers, status, booking_time)
VALUES
(:booking_id, :user_id, :train_run_id, :from_code, :to_code, :journey_date, :total_cents, :num_passengers, 'CONFIRMED', CURRENT_TIMESTAMP);

-- Insert booking seats (example loop)
INSERT INTO booking_seats
(booking_id, seat_id, passenger_name, passenger_age, passenger_gender, price_cents)
VALUES
(:booking_db_id, :seat_id, :passenger_name, :passenger_age, :passenger_gender, :price_cents);

COMMIT;

Failure handling
- If at any point a check fails (seat no longer available), ROLLBACK and inform client.
- If mock payment fails, ROLLBACK and release hold(s).

Mock payment
- Implement a `payments/mock` service that returns success/failure deterministically in dev (configurable).
- For the simplicity of initial implementation: always return success. Later add a `fail_rate` config to test failures.

Notes
- The `bookings.status` should be updated to `CANCELLED` if a booking is cancelled; record `cancellation_time`.
- Record audit/log entries on booking attempts for observability.
- Use a small `seat_holds` table if you prefer explicit holds instead of in-place `seats.status` updates.

Optional schema for holds (if not present)

CREATE TABLE seat_holds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hold_token TEXT UNIQUE NOT NULL,
  user_id INTEGER NOT NULL,
  train_run_id INTEGER NOT NULL,
  seat_ids TEXT NOT NULL, -- JSON array of seat ids or comma-separated
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME NOT NULL,
  status TEXT DEFAULT 'ACTIVE'
);

Implementation note
- Always perform the final seat status update and booking inserts inside a single DB transaction to guarantee atomicity in the face of concurrency.
