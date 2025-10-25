from fastapi import APIRouter, Query
from typing import List, Optional
import sqlite3
import os
import pathlib

router = APIRouter()

# Hardcoded DB path: backend/database/railway.db
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'railway.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/")
def search_stations(q: Optional[str] = Query(None, description="Search query for station name or code")):
    """Search stations by name or code."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if q:
            search_term = f"%{q}%"
            cur.execute("""
                SELECT code, name, state, zone, latitude, longitude, address
                FROM stations
                WHERE name LIKE ? OR code LIKE ?
                ORDER BY 
                    CASE 
                        WHEN name LIKE ? THEN 0
                        WHEN code LIKE ? THEN 1
                        ELSE 2
                    END,
                    name
                LIMIT 50
            """, (search_term, search_term, f"{q}%", f"{q}%"))
        else:
            cur.execute("""
                SELECT code, name, state, zone, latitude, longitude, address
                FROM stations
                ORDER BY name
                LIMIT 100
            """)
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.get("/{code}")
def get_station(code: str):
    """Get station details by code."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT code, name, state, zone, latitude, longitude, address
            FROM stations
            WHERE code = ?
        """, (code,))
        row = cur.fetchone()
        if not row:
            return {"error": "Station not found"}, 404
        return dict(row)
    finally:
        conn.close()
