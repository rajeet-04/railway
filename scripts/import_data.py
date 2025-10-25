#!/usr/bin/env python3
"""
scripts/import_data.py

Import stations, trains, and schedules from JSON files into the database.
Creates train_runs and seats for upcoming dates.
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DEFAULT_DB_PATH = os.environ.get("DB_PATH", "backend/database/railway.db")
STATIONS_JSON = "data/stations.json"
TRAINS_JSON = "data/trains.json"
SCHEDULES_JSON = "data/schedules.json"


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def import_stations(conn: sqlite3.Connection, stations_path: str):
    """Import stations from JSON file."""
    if not Path(stations_path).exists():
        print(f"Stations file not found at {stations_path}")
        return
    
    print(f"Loading stations from {stations_path}...")
    with open(stations_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stations = data.get('features', []) if 'features' in data else data
    
    cur = conn.cursor()
    imported = 0
    skipped = 0
    
    for station in stations:
        if isinstance(station, dict) and 'properties' in station:
            props = station['properties']
            code = props.get('code')
            name = props.get('name')
            
            if not code or not name:
                continue
            
            # Check if station already exists
            cur.execute("SELECT id FROM stations WHERE code = ?", (code,))
            if cur.fetchone():
                skipped += 1
                continue
            
            # Get coordinates if available
            geometry = station.get('geometry')
            longitude = None
            latitude = None
            if geometry and geometry.get('coordinates'):
                coords = geometry['coordinates']
                longitude = coords[0] if len(coords) > 0 else None
                latitude = coords[1] if len(coords) > 1 else None
            
            cur.execute("""
                INSERT INTO stations (code, name, state, zone, address, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                code,
                name,
                props.get('state'),
                props.get('zone'),
                props.get('address'),
                latitude,
                longitude
            ))
            imported += 1
    
    conn.commit()
    print(f"Imported {imported} stations, skipped {skipped} (already exist)")


def import_trains(conn: sqlite3.Connection, trains_path: str):
    """Import trains from JSON file."""
    if not Path(trains_path).exists():
        print(f"Trains file not found at {trains_path}")
        return
    
    print(f"Loading trains from {trains_path}...")
    with open(trains_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    trains = data.get('features', []) if 'features' in data else data
    
    cur = conn.cursor()
    imported = 0
    skipped = 0
    
    for train in trains:
        if isinstance(train, dict) and 'properties' in train:
            props = train['properties']
            number = props.get('number')
            name = props.get('name')
            
            if not number or not name:
                continue
            
            # Check if train already exists
            cur.execute("SELECT id FROM trains WHERE number = ?", (number,))
            existing = cur.fetchone()
            if existing:
                train_id = existing['id']
                skipped += 1
            else:
                # Parse duration
                duration_h = props.get('duration_h', 0)
                duration_m = props.get('duration_m', 0)
                
                cur.execute("""
                    INSERT INTO trains (
                        number, name, from_station_code, to_station_code,
                        from_station_name, to_station_name, zone, type,
                        distance_km, duration_h, duration_m,
                        departure_time, arrival_time, return_train,
                        first_ac, second_ac, third_ac, sleeper, chair_car, first_class,
                        classes, properties_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    number, name,
                    props.get('from_station_code'),
                    props.get('to_station_code'),
                    props.get('from_station_name'),
                    props.get('to_station_name'),
                    props.get('zone'),
                    props.get('type'),
                    props.get('distance_km'),
                    duration_h, duration_m,
                    props.get('departure'),
                    props.get('arrival'),
                    props.get('return_train'),
                    props.get('first_ac', 0),
                    props.get('second_ac', 0),
                    props.get('third_ac', 0),
                    props.get('sleeper', 0),
                    props.get('chair_car', 0),
                    props.get('first_class', 0),
                    props.get('classes'),
                    json.dumps(props)
                ))
                train_id = cur.lastrowid
                imported += 1
            
            # Import route geometry if available
            geometry = train.get('geometry', {})
            if geometry.get('type') == 'LineString' and geometry.get('coordinates'):
                # Check if route already exists
                cur.execute("SELECT id FROM train_routes WHERE train_id = ?", (train_id,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO train_routes (train_id, geometry_type, coordinates_json)
                        VALUES (?, ?, ?)
                    """, (train_id, 'LineString', json.dumps(geometry['coordinates'])))
    
    conn.commit()
    print(f"Imported {imported} trains, skipped {skipped} (already exist)")


def import_schedules(conn: sqlite3.Connection, schedules_path: str):
    """Import train stops/schedules from JSON file."""
    if not Path(schedules_path).exists():
        print(f"Schedules file not found at {schedules_path}")
        return
    
    print(f"Loading schedules from {schedules_path}...")
    with open(schedules_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    schedules = data.get('features', []) if 'features' in data else data

    cur = conn.cursor()
    imported = 0
    skipped = 0

    # Detect two supported formats:
    # 1) GeoJSON-like: each item has 'properties' with train_number and 'stops' list
    # 2) Flat list: each item is a stop record with keys like 'train_number', 'station_code', 'arrival', 'departure', 'day'

    if schedules and isinstance(schedules, list) and isinstance(schedules[0], dict) and 'properties' in schedules[0]:
        # Existing behavior
        for schedule in schedules:
            if not isinstance(schedule, dict) or 'properties' not in schedule:
                continue
            props = schedule['properties']
            train_number = props.get('train_number')
            if not train_number:
                continue
            cur.execute("SELECT id FROM trains WHERE number = ?", (train_number,))
            train_row = cur.fetchone()
            if not train_row:
                continue
            train_id = train_row['id']
            stops = props.get('stops', [])
            for stop in stops:
                station_code = stop.get('station_code')
                stop_sequence = stop.get('sequence')
                if not station_code or stop_sequence is None:
                    continue
                cur.execute("SELECT id FROM train_stops WHERE train_id = ? AND stop_sequence = ?", (train_id, stop_sequence))
                if cur.fetchone():
                    skipped += 1
                    continue
                try:
                    cur.execute("""
                        INSERT INTO train_stops (
                            train_id, station_code, stop_sequence,
                            arrival_time, departure_time, day_offset,
                            distance_from_start_km, platform, halt_minutes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        train_id,
                        station_code,
                        stop_sequence,
                        stop.get('arrival_time'),
                        stop.get('departure_time'),
                        stop.get('day_offset', 0),
                        stop.get('distance_from_start_km'),
                        stop.get('platform'),
                        stop.get('halt_minutes')
                    ))
                    imported += 1
                except sqlite3.IntegrityError:
                    skipped += 1
    else:
        # Flat list format: group by train_number
        from collections import defaultdict
        grouped = defaultdict(list)
        for item in schedules:
            if not isinstance(item, dict):
                continue
            tn = item.get('train_number')
            sc = item.get('station_code') or item.get('station') or item.get('station_code')
            if not tn or not sc:
                continue
            grouped[tn].append(item)

        for train_number, stops in grouped.items():
            cur.execute("SELECT id FROM trains WHERE number = ?", (train_number,))
            train_row = cur.fetchone()
            if not train_row:
                continue
            train_id = train_row['id']
            # Try to sort stops by day then by departure time (fall back to id order)
            def stop_key(s):
                day = s.get('day') if s.get('day') is not None else 1
                dep = s.get('departure') or s.get('departure_time') or ''
                return (int(day), dep or '')
            stops_sorted = sorted(stops, key=stop_key)
            for idx, stop in enumerate(stops_sorted, start=1):
                station_code = stop.get('station_code') or stop.get('station') or stop.get('station_code')
                arrival = stop.get('arrival')
                departure = stop.get('departure')
                day_offset = (int(stop.get('day')) - 1) if stop.get('day') is not None else 0
                stop_sequence = stop.get('sequence') or idx
                # Check if exists by train_id and stop_sequence
                cur.execute("SELECT id FROM train_stops WHERE train_id = ? AND stop_sequence = ?", (train_id, stop_sequence))
                if cur.fetchone():
                    skipped += 1
                    continue
                try:
                    cur.execute("""
                        INSERT INTO train_stops (
                            train_id, station_code, stop_sequence,
                            arrival_time, departure_time, day_offset
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        train_id,
                        station_code,
                        stop_sequence,
                        arrival if arrival != 'None' else None,
                        departure if departure != 'None' else None,
                        day_offset
                    ))
                    imported += 1
                except sqlite3.IntegrityError:
                    skipped += 1

    conn.commit()
    print(f"Imported {imported} train stops, skipped {skipped} (already exist)")


def create_train_runs(conn: sqlite3.Connection, days_ahead: int = 30):
    """Create train_runs for the next N days and generate seats."""
    print(f"Creating train runs for next {days_ahead} days...")
    
    cur = conn.cursor()
    
    # Get all trains
    cur.execute("SELECT id, number, name FROM trains")
    trains = cur.fetchall()
    
    today = datetime.now().date()
    runs_created = 0
    seats_created = 0
    
    for train in trains:
        train_id = train['id']
        
        for day_offset in range(days_ahead):
            run_date = today + timedelta(days=day_offset)
            run_date_str = run_date.isoformat()
            
            # Check if run already exists
            cur.execute("""
                SELECT id FROM train_runs 
                WHERE train_id = ? AND run_date = ?
            """, (train_id, run_date_str))
            
            if cur.fetchone():
                continue
            
            # Create train run
            cur.execute("""
                INSERT INTO train_runs (train_id, run_date, status, total_seats, available_seats)
                VALUES (?, ?, 'SCHEDULED', 0, 0)
            """, (train_id, run_date_str))
            
            train_run_id = cur.lastrowid
            runs_created += 1
            
            # Create seats for this run (sample: 100 seats across different classes)
            seat_configs = [
                ('1A', 20, 300000),  # First AC: 20 seats, ₹3000
                ('2A', 30, 200000),  # Second AC: 30 seats, ₹2000
                ('3A', 30, 150000),  # Third AC: 30 seats, ₹1500
                ('SL', 20, 80000),   # Sleeper: 20 seats, ₹800
            ]
            
            for seat_class, count, price_cents in seat_configs:
                for i in range(1, count + 1):
                    coach = seat_class[0]
                    seat_number = f"{seat_class}-{i}"
                    
                    cur.execute("""
                        INSERT INTO seats (
                            train_run_id, seat_number, coach_number,
                            seat_class, price_cents, status
                        ) VALUES (?, ?, ?, ?, ?, 'AVAILABLE')
                    """, (train_run_id, seat_number, f"{coach}1", seat_class, price_cents))
                    seats_created += 1
            
            # Update total and available seats
            cur.execute("""
                UPDATE train_runs 
                SET total_seats = 100, available_seats = 100
                WHERE id = ?
            """, (train_run_id,))
    
    conn.commit()
    print(f"Created {runs_created} train runs with {seats_created} seats")


def log_import(conn: sqlite3.Connection, import_type: str, status: str, message: str):
    """Log import operation."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO import_logs (import_type, status, message)
        VALUES (?, ?, ?)
    """, (import_type, status, message))
    conn.commit()


def parse_args():
    p = argparse.ArgumentParser(description="Import data from JSON files to database.")
    p.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to SQLite DB")
    p.add_argument("--stations", default=STATIONS_JSON, help="Path to stations JSON")
    p.add_argument("--trains", default=TRAINS_JSON, help="Path to trains JSON")
    p.add_argument("--schedules", default=SCHEDULES_JSON, help="Path to schedules JSON")
    p.add_argument("--days-ahead", type=int, default=30, help="Number of days to create train runs for")
    p.add_argument("--skip-runs", action="store_true", help="Skip creating train runs and seats")
    return p.parse_args()


def main():
    args = parse_args()
    
    if not Path(args.db_path).exists():
        print(f"Database not found at {args.db_path}. Please run init_db.py first.")
        sys.exit(1)
    
    conn = get_connection(args.db_path)
    
    try:
        # Import in order: stations -> trains -> schedules -> runs
        import_stations(conn, args.stations)
        log_import(conn, 'stations', 'success', f'Imported from {args.stations}')
        
        import_trains(conn, args.trains)
        log_import(conn, 'trains', 'success', f'Imported from {args.trains}')
        
        import_schedules(conn, args.schedules)
        log_import(conn, 'schedules', 'success', f'Imported from {args.schedules}')
        
        if not args.skip_runs:
            create_train_runs(conn, args.days_ahead)
            log_import(conn, 'train_runs', 'success', f'Created runs for {args.days_ahead} days')
        
        print("\nImport completed successfully!")
        
        # Print summary
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stations")
        stations_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM trains")
        trains_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM train_runs")
        runs_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM seats")
        seats_count = cur.fetchone()[0]
        
        print(f"\nDatabase summary:")
        print(f"  Stations: {stations_count}")
        print(f"  Trains: {trains_count}")
        print(f"  Train runs: {runs_count}")
        print(f"  Seats: {seats_count}")
        
    except Exception as e:
        log_import(conn, 'error', 'failed', str(e))
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
