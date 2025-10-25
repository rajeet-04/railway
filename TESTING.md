# Complete Application Test Guide

## Prerequisites
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- Database populated with train data

## Test Flow

### 1. Start Backend
```powershell
cd backend
$env:DB_PATH = 'C:\Users\rajee.RAJEET\Documents\railway\database\railway.db'
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Start Frontend
```powershell
cd frontend
npm run dev
```

### 3. User Registration Flow
1. Open `http://localhost:3000`
2. Click "Login" in header
3. Click "Register here"
4. Fill in:
   - Full Name: Test User
   - Email: test@example.com
   - Password: testpassword123
5. Click "Register"
6. Should redirect to home page with user name in header

### 4. Train Search Flow
1. On home page, fill in:
   - From Station: `NJP`
   - To Station: `HWH`
   - Journey Date: Select today or tomorrow
2. Click "Search Trains"
3. Should see list of available trains
4. Verify each train shows:
   - Train name and number
   - Departure/Arrival times
   - Duration
   - Available seats count

### 5. Booking Flow
1. From search results, click "Book Now" on any train
2. **Seat Selection Step**:
   - Click on green seats to select (they turn blue)
   - Select 2-3 seats
   - Click "Continue to Passenger Details"
3. **Passenger Details Step**:
   - Fill in name, age, gender for each passenger
   - Click "Continue to Confirmation"
4. **Confirmation Step**:
   - Review all details
   - Verify total price
   - Click "Confirm & Pay"
5. Should redirect to booking details page

### 6. View Bookings
1. Click "My Bookings" in header
2. Should see your new booking
3. Click on booking to view full details
4. Verify:
   - PNR number
   - Train details
   - Passenger list with seats
   - Payment status

### 7. Cancel Booking
1. From booking details page
2. Click "Cancel Booking"
3. Confirm cancellation
4. Status should change to "CANCELLED"

### 8. Logout
1. Click "Logout" in header
2. Should redirect to home page
3. "My Bookings" should disappear from nav
4. "Login" should appear

## API Endpoints to Test

### Public Endpoints
```bash
# Health check
curl http://localhost:8000/

# Search stations
curl "http://localhost:8000/api/stations?q=New"

# Search trains
curl "http://localhost:8000/api/trains/search?from=NJP&to=HWH&date=2025-10-25"

# Get train details
curl "http://localhost:8000/api/trains/12507?date=2025-10-25"

# Get train run seats
curl "http://localhost:8000/api/train_runs/2050/seats"
```

### Authenticated Endpoints (requires token)
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123"}'

# Get bookings (use token from login)
curl http://localhost:8000/api/bookings \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Expected Behavior

### ✅ Success Cases
- User can register and login
- Search returns trains with available seats
- Booking creates hold and finalizes transaction
- User can view all their bookings
- User can cancel confirmed bookings
- Dark/Light theme toggle works
- All pages are responsive

### ❌ Error Cases to Verify
- Cannot book without login (redirects to login page)
- Cannot select unavailable seats
- Cannot proceed without filling passenger details
- Cannot access other users' bookings
- Expired seat holds release seats

## Database Verification
```sql
-- Check user
SELECT * FROM users WHERE email = 'test@test.com';

-- Check booking
SELECT * FROM bookings WHERE user_id = 1;

-- Check seats status
SELECT status, COUNT(*) FROM seats 
WHERE train_run_id = 2050 
GROUP BY status;
```

## Troubleshooting

### Backend Issues
- **Port in use**: Kill process on port 8000
- **DB not found**: Check DB_PATH environment variable
- **No trains found**: Ensure import_data.py ran successfully

### Frontend Issues
- **API errors**: Check NEXT_PUBLIC_API_URL in .env.local
- **Lock file error**: Delete `.next/dev/lock` and restart
- **Build errors**: Run `npm install` again

### Common Fixes
```powershell
# Kill process on port
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Reset frontend
cd frontend
Remove-Item -Recurse -Force .next
npm install
npm run dev

# Restart backend
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
