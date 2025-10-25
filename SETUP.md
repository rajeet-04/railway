# Railway Booking System - Setup and Running Guide

This is a full-stack railway booking application with a FastAPI backend and Next.js frontend.

## Prerequisites

- Python 3.10+ 
- Node.js 18+ and npm
- Git LFS (for large data files)

## Project Structure

```
railway/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── database/         # Database schema and queries
├── data/             # JSON data files (stations, trains, schedules)
├── scripts/          # Database initialization and import scripts
└── docs/             # Documentation
```

## Setup Instructions

### 1. Clone and Setup Repository

```bash
git clone https://github.com/rajeet-04/railway.git
cd railway

# Pull LFS files
git lfs pull
```

### 2. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Go back to root
cd ..
```

### 3. Database Initialization

```bash
# Set environment variables for admin user
export ADMIN_EMAIL=admin@railway.com
export ADMIN_PASSWORD=Admin123456

# Initialize database with schema and create admin user
python3 scripts/init_db.py --init-schema

# Import data from JSON files (this will create train runs for next 7 days)
python3 scripts/import_data.py --days-ahead 7
```

Expected output:
- ~9,000 stations imported
- ~5,200 trains imported  
- ~36,000 train runs created (for 7 days)
- ~3.6 million seats created

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

## Running the Application

### Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### Start Frontend Server

Open a new terminal:

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Using the Application

### User Flow

1. **Search Trains**
   - Go to http://localhost:3000
   - Enter from/to station codes (e.g., NDLS for New Delhi, BCT for Mumbai Central)
   - Select journey date
   - Click "Search Trains"

2. **Register/Login**
   - Click "Login" in header
   - Register a new account or login with existing credentials
   - Admin credentials: admin@railway.com / Admin123456

3. **Book Tickets**
   - Select a train from search results
   - View seat availability
   - Select seats and enter passenger details
   - Confirm booking

4. **View Bookings**
   - Click "My Bookings" in header
   - View all your bookings
   - Click on a booking to see details

### Sample Station Codes

- NDLS - New Delhi
- BCT - Mumbai Central
- MAS - Chennai Central
- PUNE - Pune Junction
- HWH - Howrah Junction (Kolkata)
- SBC - Bangalore City

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Stations
- `GET /api/stations?q=search` - Search stations
- `GET /api/stations/{code}` - Get station by code

### Trains
- `GET /api/trains/search?from={code}&to={code}&date={date}` - Search trains
- `GET /api/trains/{number}` - Get train details

### Bookings
- `POST /api/seat_holds` - Create seat hold
- `POST /api/bookings` - Create booking
- `GET /api/bookings` - Get user bookings
- `GET /api/bookings/{booking_id}` - Get booking details
- `POST /api/bookings/{booking_id}/cancel` - Cancel booking

## Features

### Backend
- ✅ User authentication with JWT
- ✅ Train search with multiple filters
- ✅ Seat availability checking
- ✅ Transactional seat booking with hold mechanism
- ✅ Booking management (view, cancel)
- ✅ Mock payment processing
- ✅ Admin user support

### Frontend
- ✅ Dark/Light theme toggle
- ✅ Responsive design
- ✅ Train search functionality
- ✅ User registration and login
- ✅ Booking history
- ✅ Modern UI with Tailwind CSS
- ✅ Smooth animations

## Database Schema

Key tables:
- `users` - User accounts
- `stations` - Railway stations
- `trains` - Train information
- `train_stops` - Train route stops
- `train_runs` - Daily train instances
- `seats` - Available seats for each run
- `bookings` - Ticket bookings
- `booking_seats` - Passenger seat assignments

## Development

### Backend Development
```bash
cd backend
# Install dev dependencies if needed
pip install pytest pytest-cov

# Run tests
pytest

# Check API docs at http://localhost:8000/docs
```

### Frontend Development
```bash
cd frontend
# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Troubleshooting

### Database Issues
- If database is corrupted: Delete `database/railway.db` and run init script again
- If data import fails: Check JSON file integrity with `git lfs pull`

### Backend Issues
- Port 8000 already in use: Change port in uvicorn command
- Module not found: Ensure all requirements are installed

### Frontend Issues
- Build errors: Delete `.next` and `node_modules`, then `npm install` again
- API connection: Check NEXT_PUBLIC_API_URL in .env.local

## Future Enhancements

- [ ] Payment gateway integration
- [ ] Email notifications
- [ ] Train live tracking
- [ ] Seat map visualization
- [ ] Multi-language support
- [ ] Mobile app

## License

This project is for educational purposes.
