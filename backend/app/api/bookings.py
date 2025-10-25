from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os

from app.db_utils import finalize_booking_from_hold
from app.core.security import decode_token

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'railway.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user(authorization: str = Header(None)):
    """Extract and validate user from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload


class Passenger(BaseModel):
    name: str
    age: int = None
    gender: str = None


class BookingRequest(BaseModel):
    hold_id: int
    from_station_code: str
    to_station_code: str
    journey_date: str
    passengers: List[Passenger]


@router.post("/")
def create_booking(req: BookingRequest, user = Depends(get_current_user)):
    """Create a booking from a seat hold."""
    user_id = user.get("user_id")
    try:
        result = finalize_booking_from_hold(
            req.hold_id, 
            user_id, 
            req.from_station_code, 
            req.to_station_code, 
            req.journey_date, 
            [p.dict() for p in req.passengers]
        )
        return {
            "booking_id": result.get("booking_id"), 
            "status": "CONFIRMED", 
            "total_cents": result.get("total_cents")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def get_user_bookings(user = Depends(get_current_user)):
    """Get all bookings for the current user."""
    user_id = user.get("user_id")
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                b.id,
                b.booking_id,
                b.train_run_id,
                b.from_station_code,
                b.to_station_code,
                b.journey_date,
                b.booking_time,
                b.total_cents,
                b.num_passengers,
                b.status,
                b.payment_status,
                fs.name as from_station_name,
                ts.name as to_station_name,
                t.number as train_number,
                t.name as train_name
            FROM bookings b
            LEFT JOIN stations fs ON fs.code = b.from_station_code
            LEFT JOIN stations ts ON ts.code = b.to_station_code
            LEFT JOIN train_runs tr ON tr.id = b.train_run_id
            LEFT JOIN trains t ON t.id = tr.train_id
            WHERE b.user_id = ?
            ORDER BY b.booking_time DESC
        """, (user_id,))
        
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


@router.get("/{booking_id}")
def get_booking(booking_id: str, user = Depends(get_current_user)):
    """Get booking details including passengers."""
    user_id = user.get("user_id")
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Get booking info
        cur.execute("""
            SELECT 
                b.id,
                b.booking_id,
                b.user_id,
                b.train_run_id,
                b.from_station_code,
                b.to_station_code,
                b.journey_date,
                b.booking_time,
                b.total_cents,
                b.num_passengers,
                b.status,
                b.payment_status,
                b.cancellation_time,
                fs.name as from_station_name,
                ts.name as to_station_name,
                t.number as train_number,
                t.name as train_name,
                t.departure_time,
                t.arrival_time,
                tr.run_date
            FROM bookings b
            LEFT JOIN stations fs ON fs.code = b.from_station_code
            LEFT JOIN stations ts ON ts.code = b.to_station_code
            LEFT JOIN train_runs tr ON tr.id = b.train_run_id
            LEFT JOIN trains t ON t.id = tr.train_id
            WHERE b.booking_id = ?
        """, (booking_id,))
        
        booking_row = cur.fetchone()
        if not booking_row:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        booking = dict(booking_row)
        
        # Verify user owns this booking (or is admin)
        if booking['user_id'] != user_id and not user.get('is_admin'):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get passenger details
        cur.execute("""
            SELECT 
                bs.id,
                bs.passenger_name,
                bs.passenger_age,
                bs.passenger_gender,
                bs.price_cents,
                s.seat_number,
                s.coach_number,
                s.seat_class
            FROM booking_seats bs
            JOIN seats s ON s.id = bs.seat_id
            WHERE bs.booking_id = ?
        """, (booking['id'],))
        
        booking['passengers'] = [dict(row) for row in cur.fetchall()]
        
        return booking
    finally:
        conn.close()


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: str, user = Depends(get_current_user)):
    """Cancel a booking."""
    user_id = user.get("user_id")
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Get booking
        cur.execute("""
            SELECT id, user_id, status, train_run_id
            FROM bookings
            WHERE booking_id = ?
        """, (booking_id,))
        
        booking_row = cur.fetchone()
        if not booking_row:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        booking = dict(booking_row)
        
        # Verify ownership
        if booking['user_id'] != user_id and not user.get('is_admin'):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if already cancelled
        if booking['status'] == 'CANCELLED':
            raise HTTPException(status_code=400, detail="Booking already cancelled")
        
        # Begin transaction
        cur.execute("BEGIN IMMEDIATE;")
        
        # Get seat IDs
        cur.execute("""
            SELECT seat_id FROM booking_seats WHERE booking_id = ?
        """, (booking['id'],))
        
        seat_ids = [row['seat_id'] for row in cur.fetchall()]
        
        # Release seats back to AVAILABLE
        if seat_ids:
            placeholders = ','.join(['?'] * len(seat_ids))
            cur.execute(f"""
                UPDATE seats 
                SET status = 'AVAILABLE'
                WHERE id IN ({placeholders})
            """, seat_ids)
        
        # Update booking status
        cur.execute("""
            UPDATE bookings
            SET status = 'CANCELLED', cancellation_time = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (booking['id'],))
        
        # Update available seats count
        cur.execute("""
            UPDATE train_runs
            SET available_seats = available_seats + ?
            WHERE id = ?
        """, (len(seat_ids), booking['train_run_id']))
        
        cur.execute("COMMIT;")
        
        return {
            "status": "success",
            "message": "Booking cancelled successfully",
            "booking_id": booking_id
        }
    except HTTPException:
        raise
    except Exception as e:
        try:
            cur.execute("ROLLBACK;")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")
    finally:
        conn.close()
