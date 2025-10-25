from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3
import os
import pathlib

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'railway.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/{run_id}/availability")
def get_availability(
    run_id: int,
    seat_class: Optional[str] = Query(None, description="Filter by seat class")
):
    """Get seat availability for a train run."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Verify train run exists
        cur.execute("""
            SELECT id, train_id, run_date, status, total_seats, available_seats
            FROM train_runs
            WHERE id = ?
        """, (run_id,))
        
        run_row = cur.fetchone()
        if not run_row:
            raise HTTPException(status_code=404, detail="Train run not found")
        
        run_info = dict(run_row)
        
        # Get seat details
        if seat_class:
            cur.execute("""
                SELECT id, seat_number, coach_number, seat_class, price_cents, status
                FROM seats
                WHERE train_run_id = ? AND seat_class = ?
                ORDER BY coach_number, seat_number
            """, (run_id, seat_class))
        else:
            cur.execute("""
                SELECT id, seat_number, coach_number, seat_class, price_cents, status
                FROM seats
                WHERE train_run_id = ?
                ORDER BY seat_class, coach_number, seat_number
            """, (run_id,))
        
        seats = [dict(row) for row in cur.fetchall()]
        
        # Calculate summary by class
        summary = {}
        for seat in seats:
            cls = seat['seat_class']
            if cls not in summary:
                summary[cls] = {
                    'total': 0,
                    'available': 0,
                    'booked': 0,
                    'held': 0,
                    'price_cents': seat['price_cents']
                }
            summary[cls]['total'] += 1
            if seat['status'] == 'AVAILABLE':
                summary[cls]['available'] += 1
            elif seat['status'] == 'BOOKED':
                summary[cls]['booked'] += 1
            elif seat['status'] == 'HELD':
                summary[cls]['held'] += 1
        
        return {
            'train_run': run_info,
            'summary': summary,
            'seats': seats
        }
    finally:
        conn.close()


@router.get("/{run_id}/seats")
def get_seats(run_id: int):
    """Get seats for a train run (alias for availability endpoint)."""
    return get_availability(run_id)
