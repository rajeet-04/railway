-- Sample SQL Queries for Railway Reservation System Backend

-- =====================================================
-- STATION QUERIES
-- =====================================================

-- Search stations by name (autocomplete)
SELECT code, name, state, zone
FROM stations
WHERE name LIKE '%Delhi%'
   OR code LIKE '%NDLS%'
ORDER BY name
LIMIT 10;

-- Get station details with coordinates
SELECT code, name, latitude, longitude, zone, address
FROM stations
WHERE code = 'NDLS';

-- Find all stations in a state
SELECT code, name, zone, address
FROM stations
WHERE state = 'Maharashtra'
ORDER BY name;


-- =====================================================
-- TRAIN QUERIES
-- =====================================================

-- Search trains between two stations (direct trains only)
SELECT 
    t.number,
    t.name,
    t.type,
    t.from_station_name,
    t.to_station_name,
    t.departure_time,
    t.arrival_time,
    t.duration_h,
    t.duration_m,
    t.distance_km
FROM trains t
WHERE t.from_station_code = 'NDLS'
  AND t.to_station_code = 'BCT'
ORDER BY t.departure_time;

-- Get train details with class availability
SELECT 
    number,
    name,
    from_station_name,
    to_station_name,
    departure_time,
    arrival_time,
    CASE WHEN first_ac > 0 THEN 'First AC' ELSE NULL END as first_ac,
    CASE WHEN second_ac > 0 THEN 'Second AC' ELSE NULL END as second_ac,
    CASE WHEN third_ac > 0 THEN 'Third AC' ELSE NULL END as third_ac,
    CASE WHEN sleeper > 0 THEN 'Sleeper' ELSE NULL END as sleeper,
    CASE WHEN chair_car > 0 THEN 'Chair Car' ELSE NULL END as chair_car
FROM trains
WHERE number = '12345';

-- Find all trains passing through a station
SELECT DISTINCT
    t.number,
    t.name,
    t.type,
    ts.stop_sequence,
    ts.arrival_time,
    ts.departure_time
FROM trains t
JOIN train_stops ts ON t.id = ts.train_id
WHERE ts.station_code = 'NDLS'
ORDER BY ts.departure_time;


-- =====================================================
-- TRAIN ROUTE QUERIES
-- =====================================================

-- Get complete route for a train
SELECT 
    ts.stop_sequence,
    ts.station_code,
    s.name as station_name,
    ts.arrival_time,
    ts.departure_time,
    ts.day_offset,
    s.latitude,
    s.longitude
FROM train_stops ts
JOIN stations s ON ts.station_code = s.code
WHERE ts.train_id = (SELECT id FROM trains WHERE number = '12345')
ORDER BY ts.stop_sequence;

-- Check if train goes from station A to station B (with intermediate stops)
WITH route AS (
    SELECT 
        ts.train_id,
        ts.station_code,
        ts.stop_sequence
    FROM train_stops ts
    WHERE ts.train_id = (SELECT id FROM trains WHERE number = '12345')
)
SELECT 
    t.number,
    t.name,
    from_stop.stop_sequence as from_seq,
    to_stop.stop_sequence as to_seq
FROM route from_stop
JOIN route to_stop ON from_stop.train_id = to_stop.train_id
JOIN trains t ON t.id = from_stop.train_id
WHERE from_stop.station_code = 'NDLS'
  AND to_stop.station_code = 'BCT'
  AND from_stop.stop_sequence < to_stop.stop_sequence;


-- =====================================================
-- SEARCH QUERIES (Multi-hop routing)
-- =====================================================

-- Find all trains connecting two stations (direct or 1-hop transfer)
-- This is a simplified version; full A* search would be in application code

-- Direct trains
SELECT 
    t.number,
    t.name,
    'DIRECT' as journey_type,
    ts1.station_code as from_station,
    ts2.station_code as to_station,
    ts1.departure_time,
    ts2.arrival_time
FROM trains t
JOIN train_stops ts1 ON t.id = ts1.train_id
JOIN train_stops ts2 ON t.id = ts2.train_id
WHERE ts1.station_code = 'NDLS'
  AND ts2.station_code = 'BCT'
  AND ts1.stop_sequence < ts2.stop_sequence;


-- =====================================================
-- BOOKING QUERIES
-- =====================================================

-- Get available seats for a train run on a specific date
SELECT 
    s.seat_number,
    s.coach_number,
    s.seat_class,
    s.price_cents / 100.0 as price_rupees,
    s.status
FROM seats s
JOIN train_runs tr ON s.train_run_id = tr.id
JOIN trains t ON tr.train_id = t.id
WHERE t.number = '12345'
  AND tr.run_date = '2025-11-01'
  AND s.status = 'AVAILABLE'
ORDER BY s.seat_class, s.seat_number;

-- Check seat availability summary by class
SELECT 
    s.seat_class,
    COUNT(*) as total_seats,
    SUM(CASE WHEN s.status = 'AVAILABLE' THEN 1 ELSE 0 END) as available_seats,
    SUM(CASE WHEN s.status = 'BOOKED' THEN 1 ELSE 0 END) as booked_seats
FROM seats s
JOIN train_runs tr ON s.train_run_id = tr.id
JOIN trains t ON tr.train_id = t.id
WHERE t.number = '12345'
  AND tr.run_date = '2025-11-01'
GROUP BY s.seat_class;

-- Create a booking (transaction)
BEGIN TRANSACTION;

-- Check seat availability
SELECT id, status FROM seats 
WHERE train_run_id = 123 
  AND seat_number IN ('A1', 'A2') 
  AND status = 'AVAILABLE'
FOR UPDATE;

-- Update seat status
UPDATE seats 
SET status = 'BOOKED' 
WHERE train_run_id = 123 
  AND seat_number IN ('A1', 'A2') 
  AND status = 'AVAILABLE';

-- Insert booking
INSERT INTO bookings 
(booking_id, user_id, train_run_id, from_station_code, to_station_code, 
 journey_date, total_cents, num_passengers, status)
VALUES 
('PNR-2025-001234', 1, 123, 'NDLS', 'BCT', '2025-11-01', 300000, 2, 'CONFIRMED');

-- Insert booking seats
INSERT INTO booking_seats 
(booking_id, seat_id, passenger_name, passenger_age, passenger_gender, price_cents)
VALUES 
((SELECT id FROM bookings WHERE booking_id = 'PNR-2025-001234'), 
 (SELECT id FROM seats WHERE train_run_id = 123 AND seat_number = 'A1'), 
 'John Doe', 30, 'M', 150000);

COMMIT;


-- Get user's booking history
SELECT 
    b.booking_id,
    b.journey_date,
    t.number as train_number,
    t.name as train_name,
    sf.name as from_station,
    st.name as to_station,
    b.total_cents / 100.0 as total_rupees,
    b.num_passengers,
    b.status,
    b.booking_time
FROM bookings b
JOIN train_runs tr ON b.train_run_id = tr.id
JOIN trains t ON tr.train_id = t.id
JOIN stations sf ON b.from_station_code = sf.code
JOIN stations st ON b.to_station_code = st.code
WHERE b.user_id = 1
ORDER BY b.booking_time DESC;

-- Get booking details with passengers
SELECT 
    b.booking_id,
    t.number,
    t.name,
    b.journey_date,
    bs.passenger_name,
    s.seat_number,
    s.coach_number,
    s.seat_class,
    bs.price_cents / 100.0 as price_rupees
FROM bookings b
JOIN booking_seats bs ON b.id = bs.booking_id
JOIN seats s ON bs.seat_id = s.id
JOIN train_runs tr ON b.train_run_id = tr.id
JOIN trains t ON tr.train_id = t.id
WHERE b.booking_id = 'PNR-2025-001234';


-- =====================================================
-- ADMIN QUERIES
-- =====================================================

-- Daily booking statistics
SELECT 
    DATE(b.booking_time) as booking_date,
    COUNT(DISTINCT b.id) as total_bookings,
    SUM(b.num_passengers) as total_passengers,
    SUM(b.total_cents) / 100.0 as total_revenue_rupees
FROM bookings b
WHERE b.status = 'CONFIRMED'
GROUP BY DATE(b.booking_time)
ORDER BY booking_date DESC;

-- Most popular routes
SELECT 
    b.from_station_code,
    sf.name as from_station,
    b.to_station_code,
    st.name as to_station,
    COUNT(*) as booking_count,
    SUM(b.num_passengers) as total_passengers
FROM bookings b
JOIN stations sf ON b.from_station_code = sf.code
JOIN stations st ON b.to_station_code = st.code
WHERE b.status = 'CONFIRMED'
  AND b.booking_time >= DATE('now', '-30 days')
GROUP BY b.from_station_code, b.to_station_code
ORDER BY booking_count DESC
LIMIT 10;

-- Train occupancy report
SELECT 
    t.number,
    t.name,
    tr.run_date,
    tr.total_seats,
    tr.available_seats,
    (tr.total_seats - tr.available_seats) as booked_seats,
    ROUND(100.0 * (tr.total_seats - tr.available_seats) / tr.total_seats, 1) as occupancy_percent
FROM train_runs tr
JOIN trains t ON tr.train_id = t.id
WHERE tr.run_date >= DATE('now')
  AND tr.run_date <= DATE('now', '+7 days')
ORDER BY occupancy_percent DESC;


-- =====================================================
-- DIAGNOSTIC QUERIES
-- =====================================================

-- Check mapping quality
SELECT 
    warning_type,
    COUNT(*) as count,
    AVG(distance_km) as avg_distance_km
FROM mapping_warnings
GROUP BY warning_type;

-- Find trains with unmapped route segments
SELECT 
    train_number,
    COUNT(*) as unmapped_points
FROM mapping_warnings
WHERE warning_type = 'NO_STATION_NEARBY'
GROUP BY train_number
ORDER BY unmapped_points DESC
LIMIT 20;

-- Verify data completeness
SELECT 
    'Stations' as entity,
    COUNT(*) as total,
    SUM(CASE WHEN latitude IS NOT NULL THEN 1 ELSE 0 END) as with_coords
FROM stations
UNION ALL
SELECT 
    'Trains' as entity,
    COUNT(*) as total,
    COUNT(*) as with_coords
FROM trains
UNION ALL
SELECT 
    'Train Stops' as entity,
    COUNT(*) as total,
    COUNT(*) as with_coords
FROM train_stops;
