from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import sqlite3
import os
import pathlib
from datetime import datetime

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'railway.db')
print(f"Using database path: {DB_PATH}")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/search")
def search_trains(
    from_code: Optional[str] = Query(None, alias="from", description="From station code"),
    to_code: Optional[str] = Query(None, alias="to", description="To station code"),
    date: Optional[str] = Query(None, description="Journey date (YYYY-MM-DD)")
):
    """Search trains between stations on a specific date."""
    if not from_code or not to_code:
        raise HTTPException(status_code=400, detail="Both 'from' and 'to' station codes are required")
    
    if not date:
        date = datetime.now().date().isoformat()
    
    conn = get_connection()
    try:
        cur = conn.cursor()

        # First try: find trains where both stations are stops on the route and from stop is before to stop
        cur.execute("""
            SELECT
                t.id,
                t.number,
                t.name,
                t.from_station_code,
                t.to_station_code,
                t.departure_time,
                t.arrival_time,
                t.duration_h,
                t.duration_m,
                t.type,
                t.zone,
                t.classes,
                tr.id as train_run_id,
                tr.run_date,
                tr.available_seats,
                tr.total_seats,
                tr.status
            FROM trains t
            JOIN train_runs tr ON tr.train_id = t.id
            JOIN train_stops sf ON sf.train_id = t.id AND sf.station_code = ?
            JOIN train_stops st ON st.train_id = t.id AND st.station_code = ? AND st.stop_sequence > sf.stop_sequence
            WHERE tr.run_date = ? AND tr.status = 'SCHEDULED'
            GROUP BY t.id, tr.id
            ORDER BY sf.departure_time
        """, (from_code, to_code, date))

        rows = cur.fetchall()

        # Fallback: exact from/to endpoints (older behavior)
        if not rows:
            cur.execute("""
                SELECT 
                    t.id,
                    t.number,
                    t.name,
                    t.from_station_code,
                    t.to_station_code,
                    t.departure_time,
                    t.arrival_time,
                    t.duration_h,
                    t.duration_m,
                    t.type,
                    t.zone,
                    t.classes,
                    tr.id as train_run_id,
                    tr.run_date,
                    tr.available_seats,
                    tr.total_seats,
                    tr.status
                FROM trains t
                JOIN train_runs tr ON tr.train_id = t.id
                WHERE t.from_station_code = ?
                    AND t.to_station_code = ?
                    AND tr.run_date = ?
                    AND tr.status = 'SCHEDULED'
                ORDER BY t.departure_time
            """, (from_code, to_code, date))
            rows = cur.fetchall()

        results = []
        for row in rows:
            train_dict = dict(row)
            duration_str = ""
            if train_dict.get('duration_h'):
                duration_str = f"{train_dict['duration_h']}h"
            if train_dict.get('duration_m'):
                duration_str += f" {train_dict['duration_m']}m"
            train_dict['duration'] = duration_str.strip() or "N/A"
            results.append(train_dict)

        return results
    finally:
        conn.close()


@router.get("/{number}")
def get_train_details(
    number: str,
    date: Optional[str] = Query(None, description="Date to get train run info (YYYY-MM-DD)")
):
    """Get train details including route stops."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Get train basic info
        cur.execute("""
            SELECT 
                id, number, name, from_station_code, to_station_code,
                from_station_name, to_station_name, departure_time, arrival_time,
                duration_h, duration_m, type, zone, distance_km,
                first_ac, second_ac, third_ac, sleeper, chair_car, first_class,
                classes
            FROM trains
            WHERE number = ?
        """, (number,))
        
        train_row = cur.fetchone()
        if not train_row:
            raise HTTPException(status_code=404, detail="Train not found")
        
        train = dict(train_row)
        
        # Get route stops
        cur.execute("""
            SELECT 
                ts.stop_sequence,
                ts.station_code,
                s.name as station_name,
                ts.arrival_time,
                ts.departure_time,
                ts.day_offset,
                ts.distance_from_start_km,
                ts.platform,
                ts.halt_minutes
            FROM train_stops ts
            LEFT JOIN stations s ON s.code = ts.station_code
            WHERE ts.train_id = ?
            ORDER BY ts.stop_sequence
        """, (train['id'],))
        
        stops = [dict(row) for row in cur.fetchall()]
        train['stops'] = stops
        
        # Get train run info if date provided
        if date:
            cur.execute("""
                SELECT id, run_date, status, total_seats, available_seats
                FROM train_runs
                WHERE train_id = ? AND run_date = ?
            """, (train['id'], date))
            
            run_row = cur.fetchone()
            if run_row:
                train['train_run'] = dict(run_row)
        
        return train
    finally:
        conn.close()


@router.get("/{number}/runs")
def get_train_runs(
    number: str,
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get train runs for a specific train within a date range."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Get train ID
        cur.execute("SELECT id FROM trains WHERE number = ?", (number,))
        train_row = cur.fetchone()
        if not train_row:
            raise HTTPException(status_code=404, detail="Train not found")
        
        train_id = train_row['id']
        
        # Build query based on date filters
        if from_date and to_date:
            cur.execute("""
                SELECT id, run_date, status, total_seats, available_seats
                FROM train_runs
                WHERE train_id = ? AND run_date BETWEEN ? AND ?
                ORDER BY run_date
            """, (train_id, from_date, to_date))
        elif from_date:
            cur.execute("""
                SELECT id, run_date, status, total_seats, available_seats
                FROM train_runs
                WHERE train_id = ? AND run_date >= ?
                ORDER BY run_date
                LIMIT 30
            """, (train_id, from_date))
        else:
            # Default: next 30 days from today
            today = datetime.now().date().isoformat()
            cur.execute("""
                SELECT id, run_date, status, total_seats, available_seats
                FROM train_runs
                WHERE train_id = ? AND run_date >= ?
                ORDER BY run_date
                LIMIT 30
            """, (train_id, today))
        
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


@router.get("/{number}/journey")
def get_journey_details(
    number: str,
    from_code: str = Query(..., alias="from", description="From station code"),
    to_code: str = Query(..., alias="to", description="To station code"),
    date: str = Query(..., description="Journey date (YYYY-MM-DD)")
):
    """Get journey-specific details including segment stops, timings, and pricing."""
    import math
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Get train basic info
        cur.execute("""
            SELECT 
                id, number, name, from_station_code, to_station_code,
                from_station_name, to_station_name, departure_time, arrival_time,
                duration_h, duration_m, type, zone,
                first_ac, second_ac, third_ac, sleeper, chair_car, first_class
            FROM trains
            WHERE number = ?
        """, (number,))
        
        train_row = cur.fetchone()
        if not train_row:
            raise HTTPException(status_code=404, detail="Train not found")
        
        train = dict(train_row)
        
        # Get journey segment stops
        cur.execute("""
            SELECT 
                ts.stop_sequence,
                ts.station_code,
                s.name as station_name,
                s.latitude,
                s.longitude,
                ts.arrival_time,
                ts.departure_time,
                ts.day_offset,
                ts.platform,
                ts.halt_minutes
            FROM train_stops ts
            LEFT JOIN stations s ON s.code = ts.station_code
            WHERE ts.train_id = ?
                AND ts.stop_sequence >= (
                    SELECT stop_sequence FROM train_stops 
                    WHERE train_id = ? AND station_code = ?
                )
                AND ts.stop_sequence <= (
                    SELECT stop_sequence FROM train_stops 
                    WHERE train_id = ? AND station_code = ?
                )
            ORDER BY ts.stop_sequence
        """, (train['id'], train['id'], from_code, train['id'], to_code))
        
        stops = [dict(row) for row in cur.fetchall()]
        
        if len(stops) < 2:
            raise HTTPException(status_code=404, detail="Journey segment not found")
        
        # Calculate total distance using Haversine formula
        def haversine(lat1, lon1, lat2, lon2):
            """Calculate distance between two points on Earth in kilometers."""
            R = 6371  # Earth's radius in kilometers
            
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            
            a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            return R * c
        
        # Calculate cumulative distance for each stop
        total_distance = 0
        for i in range(len(stops)):
            if i == 0:
                stops[i]['distance_from_start'] = 0
            else:
                prev_stop = stops[i-1]
                curr_stop = stops[i]
                
                if (prev_stop.get('latitude') and prev_stop.get('longitude') and 
                    curr_stop.get('latitude') and curr_stop.get('longitude')):
                    segment_distance = haversine(
                        prev_stop['latitude'], prev_stop['longitude'],
                        curr_stop['latitude'], curr_stop['longitude']
                    )
                    total_distance += segment_distance
                    stops[i]['distance_from_start'] = round(total_distance, 2)
                else:
                    stops[i]['distance_from_start'] = None
        
        # Calculate duration
        from_stop = stops[0]
        to_stop = stops[-1]
        
        # Parse time and calculate duration
        def parse_time(time_str, day_offset):
            if not time_str:
                return None
            h, m, s = map(int, time_str.split(':'))
            return (day_offset * 24 * 60) + (h * 60) + m
        
        from_mins = parse_time(from_stop.get('departure_time'), from_stop.get('day_offset', 0))
        to_mins = parse_time(to_stop.get('arrival_time'), to_stop.get('day_offset', 0))
        
        journey_duration_mins = None
        journey_duration_str = "N/A"
        if from_mins is not None and to_mins is not None:
            journey_duration_mins = to_mins - from_mins
            hours = journey_duration_mins // 60
            mins = journey_duration_mins % 60
            journey_duration_str = f"{hours}h {mins}m"
        
        # Get train run info
        cur.execute("""
            SELECT id, run_date, status, total_seats, available_seats
            FROM train_runs
            WHERE train_id = ? AND run_date = ?
        """, (train['id'], date))
        
        run_row = cur.fetchone()
        train_run = dict(run_row) if run_row else None
        
        # Calculate base pricing per km (₹ per km based on class)
        # Pricing structure: 3A > 2A > 1A > CC > SL > GEN
        base_rates_per_km = {
            '3A': 6.50,   # Third AC (Most expensive)
            '2A': 5.00,   # Second AC
            '1A': 4.00,   # First AC
            'CC': 2.50,   # Chair Car
            'SL': 1.50,   # Sleeper
            'FC': 3.00,   # First Class
            'GEN': 0.50   # General
        }
        
        # Map database fields to class codes
        class_availability = {}
        if train.get('first_ac'):
            class_availability['1A'] = True
        if train.get('second_ac'):
            class_availability['2A'] = True
        if train.get('third_ac'):
            class_availability['3A'] = True
        if train.get('sleeper'):
            class_availability['SL'] = True
        if train.get('chair_car'):
            class_availability['CC'] = True
        if train.get('first_class'):
            class_availability['FC'] = True
        
        # Calculate pricing for available classes
        pricing = {}
        if total_distance > 0:
            for class_code, available in class_availability.items():
                if available and class_code in base_rates_per_km:
                    base_fare = total_distance * base_rates_per_km[class_code]
                    # Add reservation charge
                    reservation_charge = 20 if class_code in ['1A', '2A', '3A'] else 15
                    total_fare = base_fare + reservation_charge
                    pricing[class_code] = {
                        'base_fare': round(base_fare, 2),
                        'reservation_charge': reservation_charge,
                        'total_fare': round(total_fare, 2),
                        'total_fare_cents': int(total_fare * 100)
                    }
        
        return {
            'train': {
                'id': train['id'],
                'number': train['number'],
                'name': train['name'],
                'type': train['type']
            },
            'journey': {
                'from_station_code': from_code,
                'from_station_name': from_stop['station_name'],
                'to_station_code': to_code,
                'to_station_name': to_stop['station_name'],
                'departure_time': from_stop.get('departure_time'),
                'arrival_time': to_stop.get('arrival_time'),
                'departure_day_offset': from_stop.get('day_offset', 0),
                'arrival_day_offset': to_stop.get('day_offset', 0),
                'duration': journey_duration_str,
                'distance_km': round(total_distance, 2) if total_distance > 0 else None
            },
            'stops': stops,
            'pricing': pricing,
            'train_run': train_run
        }
    finally:
        conn.close()


@router.get("/{number}/seats")
def get_train_seats(
    number: str,
    date: str = Query(..., description="Journey date (YYYY-MM-DD)"),
    from_code: Optional[str] = Query(None, alias="from", description="From station code for pricing"),
    to_code: Optional[str] = Query(None, alias="to", description="To station code for pricing")
):
    """Get seats for a train on a specific date with journey-specific pricing."""
    import math
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Get train run ID and train info
        cur.execute("""
            SELECT tr.id, t.id as train_id
            FROM trains t
            JOIN train_runs tr ON tr.train_id = t.id
            WHERE t.number = ? AND tr.run_date = ?
        """, (number, date))
        
        run_row = cur.fetchone()
        if not run_row:
            raise HTTPException(status_code=404, detail="Train run not found")
        
        run_id = run_row['id']
        train_id = run_row['train_id']
        
        # Get seats
        cur.execute("""
            SELECT id, seat_number, coach_number, seat_class, price_cents, status
            FROM seats
            WHERE train_run_id = ?
            ORDER BY seat_class, coach_number, seat_number
        """, (run_id,))
        
        seats = [dict(row) for row in cur.fetchall()]
        
        # If from/to provided, calculate distance-based pricing
        if from_code and to_code:
            # Get stations with coordinates
            cur.execute("""
                SELECT 
                    ts.stop_sequence,
                    ts.station_code,
                    s.latitude,
                    s.longitude
                FROM train_stops ts
                LEFT JOIN stations s ON s.code = ts.station_code
                WHERE ts.train_id = ?
                    AND ts.stop_sequence >= (
                        SELECT stop_sequence FROM train_stops 
                        WHERE train_id = ? AND station_code = ?
                    )
                    AND ts.stop_sequence <= (
                        SELECT stop_sequence FROM train_stops 
                        WHERE train_id = ? AND station_code = ?
                    )
                ORDER BY ts.stop_sequence
            """, (train_id, train_id, from_code, train_id, to_code))
            
            stops = [dict(row) for row in cur.fetchall()]
            
            # Calculate distance
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371
                lat1_rad = math.radians(lat1)
                lat2_rad = math.radians(lat2)
                delta_lat = math.radians(lat2 - lat1)
                delta_lon = math.radians(lon2 - lon1)
                a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c
            
            total_distance = 0
            for i in range(1, len(stops)):
                prev = stops[i-1]
                curr = stops[i]
                if (prev.get('latitude') and prev.get('longitude') and 
                    curr.get('latitude') and curr.get('longitude')):
                    total_distance += haversine(
                        prev['latitude'], prev['longitude'],
                        curr['latitude'], curr['longitude']
                    )
            
            # Update seat prices based on distance
            # Pricing structure: 3A > 2A > 1A > CC > SL > GEN
            base_rates_per_km = {
                '3A': 6.50, '2A': 5.00, '1A': 4.00,
                'CC': 2.50, 'SL': 1.50, 'FC': 3.00, 'GEN': 0.50
            }
            
            for seat in seats:
                class_code = seat['seat_class']
                if class_code in base_rates_per_km and total_distance > 0:
                    base_fare = total_distance * base_rates_per_km[class_code]
                    reservation = 20 if class_code in ['1A', '2A', '3A'] else 15
                    total_fare = base_fare + reservation
                    seat['price_cents'] = int(total_fare * 100)
                    seat['distance_km'] = round(total_distance, 2)
        
        return {
            'seats': seats
        }
    finally:
        conn.close()
