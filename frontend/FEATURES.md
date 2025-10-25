# Railway Booking System - Frontend Features

## ✅ Completed Features

### Pages
1. **Home/Landing Page** (`/`)
   - Train search form with from/to station and date picker
   - Feature highlights
   - Redirects to search results

2. **Search Results Page** (`/search`)
   - Displays available trains for selected route and date
   - Shows train details: name, number, type, departure/arrival times, duration
   - Real-time seat availability
   - Book now button for each train

3. **Booking Flow** (`/book/[trainRunId]`)
   - **Step 1: Seat Selection**
     - Visual seat map grouped by class (1A, 2A, 3A, SL, etc.)
     - Color-coded seats (green=available, gray=booked, blue=selected)
     - Click to select/deselect seats
   - **Step 2: Passenger Details**
     - Form for each passenger (name, age, gender)
     - Auto-populate based on selected seats
   - **Step 3: Confirmation**
     - Review journey details
     - Review passenger and seat assignments
     - Total price calculation
     - Confirm & Pay button

4. **My Bookings** (`/bookings`)
   - List of all user bookings
   - Status badges (CONFIRMED, CANCELLED)
   - Quick view of journey details
   - Link to detailed booking view

5. **Booking Details** (`/bookings/[id]`)
   - Complete PNR details
   - Train and journey information
   - Passenger list with seat assignments
   - Payment status
   - Cancel booking functionality

6. **Authentication**
   - Login page (`/auth/login`)
   - Register page (`/auth/register`)
   - JWT token-based authentication
   - Persistent login state

### Components
1. **Header**
   - Logo and navigation
   - Dark/Light theme toggle
   - User greeting when logged in
   - Conditional navigation (shows "My Bookings" only when logged in)
   - Logout functionality

2. **ThemeProvider**
   - Dark/Light mode support
   - Persists theme preference

### Features
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Dark mode support
- ✅ Real-time seat availability
- ✅ Secure authentication with JWT
- ✅ Form validation
- ✅ Loading states and error handling
- ✅ Route-based train search (finds trains with intermediate stops)
- ✅ Transaction-based booking with seat holds
- ✅ Booking cancellation

## 🎨 Design System
- **Colors**: Custom accent colors with dark mode variants
- **Typography**: Clean, modern font hierarchy
- **Components**: Tailwind CSS for styling
- **Animations**: Smooth transitions and hover effects

## 🚀 How to Use

### For Users
1. **Search for Trains**
   - Enter from/to station codes (e.g., NJP, HWH, NDLS)
   - Select journey date
   - Click "Search Trains"

2. **Book Tickets**
   - Choose a train from search results
   - Select seats from the seat map
   - Fill in passenger details
   - Review and confirm booking

3. **View Bookings**
   - Navigate to "My Bookings"
   - Click on any booking to see full details
   - Cancel if needed

### Sample Station Codes
- **NJP** - New Jalpaiguri
- **HWH** - Howrah Junction (Kolkata)
- **NDLS** - New Delhi
- **BCT** - Mumbai Central
- **MAS** - Chennai Central
- **PUNE** - Pune Junction
- **SBC** - Bangalore City

## 🔧 Technical Details

### State Management
- Client-side state with React hooks
- LocalStorage for auth token and user data
- No external state management library needed

### API Integration
- RESTful API calls to backend
- Environment variable for API URL (`NEXT_PUBLIC_API_URL`)
- Error handling with user-friendly messages

### Routing
- Next.js App Router
- Dynamic routes for bookings and train runs
- URL parameters for search state

### Authentication Flow
1. User registers/logs in
2. Backend returns JWT token
3. Token stored in localStorage
4. Token sent with all authenticated requests
5. Logout clears token and user data

## 🐛 Known Issues & Future Improvements
- [ ] Add station code autocomplete
- [ ] Add seat map visualization
- [ ] Add email notifications
- [ ] Add payment gateway integration
- [ ] Add booking history filtering/sorting
- [ ] Add mobile app
- [ ] Add real-time train tracking
- [ ] Add multi-language support
