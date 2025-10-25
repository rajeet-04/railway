import os
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict

import pathlib

# Hardcoded DB path: backend/database/railway.db
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'railway.db')


def get_connection(path: Optional[str] = None) -> sqlite3.Connection:
    p = path or DB_PATH
    conn = sqlite3.connect(p, timeout=30, isolation_level=None)  # autocommit disabled via explicit transactions
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_user(email: str, password_hash: str, full_name: str, phone: Optional[str] = None, is_admin: bool = False) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (email, password_hash, full_name, phone, is_admin, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    (email, password_hash, full_name, phone, 1 if is_admin else 0))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# Seat hold helpers (simple implementation using a seat_holds table)
def ensure_seat_holds_table():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS seat_holds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hold_token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            train_run_id INTEGER NOT NULL,
            seat_ids TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            status TEXT DEFAULT 'ACTIVE'
        );
        """)
        conn.commit()
    finally:
        conn.close()


def create_seat_hold(user_id: int, train_run_id: int, seat_ids: List[int], hold_seconds: int = 120) -> Dict:
    ensure_seat_holds_table()
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Begin immediate transaction to lock writer
        cur.execute("BEGIN IMMEDIATE;")
        # Verify seats are available
        q = f"SELECT id FROM seats WHERE train_run_id = ? AND id IN ({','.join(['?']*len(seat_ids))}) AND status = 'AVAILABLE'"
        params = [train_run_id] + seat_ids
        cur.execute(q, params)
        rows = cur.fetchall()
        if len(rows) != len(seat_ids):
            cur.execute("ROLLBACK;")
            raise Exception("One or more seats are not available")
        # Create hold
        hold_token = str(uuid.uuid4())
        expires_at = (datetime.utcnow() + timedelta(seconds=hold_seconds)).isoformat()
        cur.execute("INSERT INTO seat_holds (hold_token, user_id, train_run_id, seat_ids, expires_at) VALUES (?, ?, ?, ?, ?)",
                    (hold_token, user_id, train_run_id, json.dumps(seat_ids), expires_at))
        hold_id = cur.lastrowid
        # Mark seats as HELD
        update_q = f"UPDATE seats SET status = 'HELD' WHERE train_run_id = ? AND id IN ({','.join(['?']*len(seat_ids))})"
        cur.execute(update_q, params)
        cur.execute("COMMIT;")
        return {"hold_id": hold_id, "hold_token": hold_token, "expires_at": expires_at}
    except Exception as e:
        try:
            cur.execute("ROLLBACK;")
        except Exception:
            pass
        raise
    finally:
        conn.close()


def release_seat_hold(hold_id: int) -> None:
    ensure_seat_holds_table()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT seat_ids, status FROM seat_holds WHERE id = ?", (hold_id,))
        row = cur.fetchone()
        if not row:
            return
        seat_ids = json.loads(row["seat_ids"])
        cur.execute("BEGIN IMMEDIATE;")
        # Update seats back to AVAILABLE only if currently HELD
        q = f"UPDATE seats SET status = 'AVAILABLE' WHERE id IN ({','.join(['?']*len(seat_ids))}) AND status = 'HELD'"
        cur.execute(q, seat_ids)
        cur.execute("UPDATE seat_holds SET status = 'RELEASED' WHERE id = ?", (hold_id,))
        cur.execute("COMMIT;")
    except Exception:
        try:
            cur.execute("ROLLBACK;")
        except Exception:
            pass
        raise
    finally:
        conn.close()


def finalize_booking_from_hold(hold_id: int, user_id: int, from_code: str, to_code: str, journey_date: str, passengers: List[Dict]) -> Dict:
    """Finalize booking given a valid hold. Returns booking_id and booking db id."""
    ensure_seat_holds_table()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE;")
        cur.execute("SELECT id, seat_ids, train_run_id, user_id, expires_at, status FROM seat_holds WHERE id = ?", (hold_id,))
        hold = cur.fetchone()
        if not hold:
            cur.execute("ROLLBACK;")
            raise Exception("Hold not found")
        if hold["status"] != 'ACTIVE':
            cur.execute("ROLLBACK;")
            raise Exception("Hold is not active")
        if hold["user_id"] != user_id:
            cur.execute("ROLLBACK;")
            raise Exception("Hold does not belong to user")
        expires_at = datetime.fromisoformat(hold["expires_at"])
        if datetime.utcnow() > expires_at:
            cur.execute("ROLLBACK;")
            raise Exception("Hold expired")
        seat_ids = json.loads(hold["seat_ids"])
        train_run_id = hold["train_run_id"]
        # verify seats are still HELD
        q = f"SELECT id FROM seats WHERE train_run_id = ? AND id IN ({','.join(['?']*len(seat_ids))}) AND status = 'HELD'"
        params = [train_run_id] + seat_ids
        cur.execute(q, params)
        rows = cur.fetchall()
        if len(rows) != len(seat_ids):
            cur.execute("ROLLBACK;")
            raise Exception("One or more seats no longer held")
        # Create booking record
        booking_id = f"PNR-{int(datetime.utcnow().timestamp())}-{str(uuid.uuid4())[:6].upper()}"
        total_cents = 0
        num_passengers = len(passengers)
        # compute total from seats
        select_q = f"SELECT price_cents FROM seats WHERE id IN ({','.join(['?']*len(seat_ids))})"
        cur.execute(select_q, seat_ids)
        prices = [r[0] for r in cur.fetchall()]
        total_cents = sum(prices)
        cur.execute("INSERT INTO bookings (booking_id, user_id, train_run_id, from_station_code, to_station_code, journey_date, total_cents, num_passengers, status, payment_status, booking_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', 'PAID', CURRENT_TIMESTAMP)",
                    (booking_id, user_id, train_run_id, from_code, to_code, journey_date, total_cents, num_passengers))
        booking_db_id = cur.lastrowid
        # Insert booking seats
        for seat_id, passenger in zip(seat_ids, passengers):
            price = cur.execute("SELECT price_cents FROM seats WHERE id = ?", (seat_id,)).fetchone()[0]
            cur.execute("INSERT INTO booking_seats (booking_id, seat_id, passenger_name, passenger_age, passenger_gender, price_cents) VALUES (?, ?, ?, ?, ?, ?)",
                        (booking_db_id, seat_id, passenger.get('name'), passenger.get('age'), passenger.get('gender'), price))
        # Mark seats as BOOKED
        update_q = f"UPDATE seats SET status = 'BOOKED' WHERE id IN ({','.join(['?']*len(seat_ids))})"
        cur.execute(update_q, seat_ids)
        # Mark hold completed
        cur.execute("UPDATE seat_holds SET status = 'COMPLETED' WHERE id = ?", (hold_id,))
        cur.execute("COMMIT;")
        return {"booking_id": booking_id, "booking_db_id": booking_db_id, "total_cents": total_cents}
    except Exception:
        try:
            cur.execute("ROLLBACK;")
        except Exception:
            pass
        raise
    finally:
        conn.close()


def get_train_runs_between(from_code: str, to_code: str, date: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT t.number as train_number, t.name as train_name, tr.id as train_run_id, tr.run_date
        FROM trains t
        JOIN train_runs tr ON tr.train_id = t.id
        WHERE t.from_station_code = ? AND t.to_station_code = ? AND tr.run_date = ?
        ORDER BY tr.run_date
        """, (from_code, to_code, date))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_availability_for_run(run_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, seat_number, coach_number, seat_class, price_cents, status FROM seats WHERE train_run_id = ?", (run_id,))
        rows = cur.fetchall()
        seats = [dict(r) for r in rows]
        # summary
        summary = {}
        for s in seats:
            cls = s['seat_class']
            if cls not in summary:
                summary[cls] = {'total': 0, 'available': 0}
            summary[cls]['total'] += 1
            if s['status'] == 'AVAILABLE':
                summary[cls]['available'] += 1
        return {'seats': seats, 'summary': summary}
    finally:
        conn.close()
