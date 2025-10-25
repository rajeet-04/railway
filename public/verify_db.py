#!/usr/bin/env python3
"""
Database verification script - check data quality and statistics
"""

import sqlite3
from pathlib import Path


def verify_database(db_path: str):
    """Run comprehensive database verification."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("="*60)
    print("DATABASE VERIFICATION REPORT")
    print("="*60)
    
    # Basic counts
    print("\n1. RECORD COUNTS")
    print("-" * 60)
    
    tables = [
        ('stations', 'Stations'),
        ('trains', 'Trains'),
        ('train_routes', 'Train Routes'),
        ('train_stops', 'Train Stops'),
        ('train_runs', 'Train Runs'),
        ('users', 'Users'),
        ('bookings', 'Bookings'),
        ('mapping_warnings', 'Mapping Warnings'),
    ]
    
    for table, label in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{label:.<40} {count:>15,}")
    
    # Stations with coordinates
    print("\n2. STATION QUALITY")
    print("-" * 60)
    cursor.execute("SELECT COUNT(*) FROM stations WHERE latitude IS NOT NULL")
    with_coords = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM stations")
    total_stations = cursor.fetchone()[0]
    
    pct = 100 * with_coords / total_stations if total_stations > 0 else 0
    print(f"Stations with coordinates............... {with_coords:>8,} / {total_stations:>8,} ({pct:.1f}%)")
    
    # Trains with routes
    print("\n3. TRAIN QUALITY")
    print("-" * 60)
    cursor.execute("""
        SELECT COUNT(DISTINCT t.id) 
        FROM trains t 
        JOIN train_routes tr ON t.id = tr.train_id
    """)
    with_routes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM trains")
    total_trains = cursor.fetchone()[0]
    
    pct = 100 * with_routes / total_trains if total_trains > 0 else 0
    print(f"Trains with route geometry.............. {with_routes:>8,} / {total_trains:>8,} ({pct:.1f}%)")
    
    # Trains with stops
    cursor.execute("""
        SELECT COUNT(DISTINCT train_id) 
        FROM train_stops
    """)
    with_stops = cursor.fetchone()[0]
    pct = 100 * with_stops / total_trains if total_trains > 0 else 0
    print(f"Trains with stop schedules.............. {with_stops:>8,} / {total_trains:>8,} ({pct:.1f}%)")
    
    # Average stops per train
    cursor.execute("""
        SELECT AVG(stop_count) 
        FROM (
            SELECT COUNT(*) as stop_count 
            FROM train_stops 
            GROUP BY train_id
        )
    """)
    result = cursor.fetchone()
    avg_stops = result[0] if result and result[0] else 0
    print(f"Average stops per train................. {avg_stops:>15.1f}")
    
    # Mapping quality
    print("\n4. ROUTE MAPPING QUALITY")
    print("-" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM mapping_warnings WHERE warning_type = 'LARGE_DISTANCE'")
    large_dist = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM mapping_warnings WHERE warning_type = 'NO_STATION_NEARBY'")
    no_station = cursor.fetchone()[0]
    
    print(f"Large distance warnings................. {large_dist:>15,}")
    print(f"No station nearby warnings.............. {no_station:>15,}")
    
    if large_dist + no_station > 0:
        cursor.execute("""
            SELECT AVG(distance_km) 
            FROM mapping_warnings 
            WHERE warning_type = 'LARGE_DISTANCE'
        """)
        result = cursor.fetchone()
        avg_dist = result[0] if result and result[0] else 0
        print(f"Average large distance.................. {avg_dist:>15.2f} km")
    
    # Train types
    print("\n5. TRAIN DISTRIBUTION")
    print("-" * 60)
    
    cursor.execute("""
        SELECT type, COUNT(*) as count 
        FROM trains 
        WHERE type IS NOT NULL
        GROUP BY type 
        ORDER BY count DESC 
        LIMIT 10
    """)
    
    for train_type, count in cursor.fetchall():
        print(f"{train_type:.<40} {count:>15,}")
    
    # Top zones
    print("\n6. TOP RAILWAY ZONES")
    print("-" * 60)
    
    cursor.execute("""
        SELECT zone, COUNT(*) as count 
        FROM stations 
        WHERE zone IS NOT NULL
        GROUP BY zone 
        ORDER BY count DESC 
        LIMIT 10
    """)
    
    for zone, count in cursor.fetchall():
        print(f"{zone:.<40} {count:>15,}")
    
    # Sample trains
    print("\n7. SAMPLE TRAINS")
    print("-" * 60)
    
    cursor.execute("""
        SELECT 
            t.number,
            t.name,
            t.from_station_name,
            t.to_station_name,
            COUNT(ts.id) as stops
        FROM trains t
        LEFT JOIN train_stops ts ON t.id = ts.train_id
        GROUP BY t.id
        ORDER BY RANDOM()
        LIMIT 5
    """)
    
    for number, name, from_st, to_st, stops in cursor.fetchall():
        print(f"{number} {name}")
        print(f"  {from_st} → {to_st}")
        print(f"  Stops: {stops}")
        print()
    
    # Database size
    print("\n8. DATABASE SIZE")
    print("-" * 60)
    
    db_file = Path(db_path)
    if db_file.exists():
        size_mb = db_file.stat().st_size / (1024 * 1024)
        print(f"Database file size...................... {size_mb:>12.2f} MB")
    
    # Index info
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sqlite_master 
        WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
    """)
    index_count = cursor.fetchone()[0]
    print(f"Number of indexes....................... {index_count:>15,}")
    
    print("\n" + "="*60)
    print("✓ Verification complete")
    print("="*60)
    
    conn.close()


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'database' / 'railway.db'
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Run 'python scripts/import_data.py' first")
        exit(1)
    
    verify_database(str(db_path))
