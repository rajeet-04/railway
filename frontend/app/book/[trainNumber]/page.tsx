'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface Seat {
  id: number;
  seat_number: string;
  coach_number: string;
  seat_class: string;
  price_cents: number;
  status: string;
}

interface Passenger {
  name: string;
  age: string;
  gender: string;
}

export default function BookPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const trainNumber = params.trainNumber as string;
  const from = searchParams.get('from');
  const to = searchParams.get('to');
  const date = searchParams.get('date');

  const [seats, setSeats] = useState<Seat[]>([]);
  const [selectedSeats, setSelectedSeats] = useState<number[]>([]);
  const [passengers, setPassengers] = useState<Passenger[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [step, setStep] = useState<'seats' | 'passengers' | 'confirm'>('seats');
  const [booking, setBooking] = useState(false);

  const fetchSeats = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/trains/${trainNumber}/seats?date=${date}&from=${from}&to=${to}`);

      if (!response.ok) {
        throw new Error('Failed to fetch seats');
      }

      const data = await response.json();
      setSeats(data.seats || []);
    } catch (err) {
      setError('Failed to load seats. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [trainNumber, date, from, to]);

  useEffect(() => {
    fetchSeats();
  }, [fetchSeats]);

  const toggleSeat = (seatId: number) => {
    const index = selectedSeats.indexOf(seatId);
    if (index !== -1) {
      // Deselect: remove the seat and the corresponding passenger
      setSelectedSeats(selectedSeats.filter(id => id !== seatId));
      setPassengers(passengers.filter((_, i) => i !== index));
    } else {
      // Select: add the seat and a new passenger
      setSelectedSeats([...selectedSeats, seatId]);
      setPassengers([...passengers, { name: '', age: '', gender: 'M' }]);
    }
  };

  const updatePassenger = (index: number, field: keyof Passenger, value: string) => {
    const updated = [...passengers];
    updated[index] = { ...updated[index], [field]: value };
    setPassengers(updated);
  };

  const handleBook = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Please login to book tickets');
      router.push('/auth/login');
      return;
    }

    // Validate passengers
    for (const p of passengers) {
      if (!p.name || !p.age || !p.gender) {
        alert('Please fill in all passenger details');
        return;
      }
    }

    setBooking(true);
    setError('');

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // First, get the train run ID from train number and date
      const trainResponse = await fetch(`${apiUrl}/api/trains/${trainNumber}?date=${date}`);
      if (!trainResponse.ok) {
        throw new Error('Failed to get train details');
      }
      const trainData = await trainResponse.json();
      const trainRunId = trainData.train_run?.id;
      if (!trainRunId) {
        throw new Error('No train run found for this date');
      }

      // Step 1: Create seat hold
      const holdResponse = await fetch(`${apiUrl}/api/seat_holds`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          train_run_id: trainRunId,
          seat_ids: selectedSeats,
        }),
      });

      if (!holdResponse.ok) {
        const data = await holdResponse.json();
        throw new Error(data.detail || 'Failed to hold seats');
      }

      const holdData = await holdResponse.json();

      // Step 2: Create booking
      const bookingResponse = await fetch(`${apiUrl}/api/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          hold_id: holdData.hold_id,
          from_station_code: from,
          to_station_code: to,
          journey_date: date,
          passengers: passengers.map(p => ({
            name: p.name,
            age: parseInt(p.age),
            gender: p.gender,
          })),
        }),
      });

      if (!bookingResponse.ok) {
        const data = await bookingResponse.json();
        throw new Error(data.detail || 'Failed to create booking');
      }

      const bookingData = await bookingResponse.json();
      
      // Redirect to booking details
      router.push(`/bookings/${bookingData.booking_id}`);
    } catch (err: any) {
      setError(err.message || 'Booking failed. Please try again.');
      console.error(err);
    } finally {
      setBooking(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="animate-pulse bg-surface h-96 rounded-lg"></div>
      </div>
    );
  }

  if (error && !booking) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  const selectedSeatObjects = seats.filter(s => selectedSeats.includes(s.id)).sort((a, b) => selectedSeats.indexOf(a.id) - selectedSeats.indexOf(b.id));
  const totalPrice = selectedSeatObjects.reduce((sum, seat) => sum + seat.price_cents, 0);

  // Group seats by class for display
  const seatsByClass = seats.reduce((acc, seat) => {
    if (!acc[seat.seat_class]) {
      acc[seat.seat_class] = [];
    }
    acc[seat.seat_class].push(seat);
    return acc;
  }, {} as Record<string, Seat[]>);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Book Your Tickets</h1>
        <p className="text-gray-600 dark:text-gray-400">
          {from} → {to} on {date}
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center mb-8">
        <div className="flex items-center">
          <div className={`flex items-center justify-center w-10 h-10 rounded-full ${step === 'seats' ? 'bg-accent text-white' : 'bg-gray-300 dark:bg-gray-700'}`}>
            1
          </div>
          <div className="w-24 h-1 bg-gray-300 dark:bg-gray-700 mx-2"></div>
          <div className={`flex items-center justify-center w-10 h-10 rounded-full ${step === 'passengers' ? 'bg-accent text-white' : 'bg-gray-300 dark:bg-gray-700'}`}>
            2
          </div>
          <div className="w-24 h-1 bg-gray-300 dark:bg-gray-700 mx-2"></div>
          <div className={`flex items-center justify-center w-10 h-10 rounded-full ${step === 'confirm' ? 'bg-accent text-white' : 'bg-gray-300 dark:bg-gray-700'}`}>
            3
          </div>
        </div>
      </div>

      {step === 'seats' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Select Seats ({selectedSeats.length} selected)</h2>
          
          <div className="space-y-6">
            {Object.entries(seatsByClass).map(([className, classSeats]) => (
              <div key={className} className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4">Class: {className}</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {classSeats.map((seat) => (
                    <button
                      key={seat.id}
                      onClick={() => seat.status === 'AVAILABLE' && toggleSeat(seat.id)}
                      disabled={seat.status !== 'AVAILABLE'}
                      className={`p-3 rounded-lg text-sm font-semibold transition-all flex flex-col items-center justify-center min-h-[80px] ${
                        selectedSeats.includes(seat.id)
                          ? 'bg-accent text-white'
                          : seat.status === 'AVAILABLE'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      <span className="text-base">{seat.seat_number}</span>
                      {seat.status === 'AVAILABLE' && (
                        <span className="text-xs mt-1 opacity-80">
                          ₹{(seat.price_cents / 100).toFixed(0)}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {selectedSeats.length > 0 && (
            <div className="mt-6 bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-500">Selected Seats</p>
                  <p className="font-semibold text-lg">{selectedSeats.length} seat(s)</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Total Amount</p>
                  <p className="font-bold text-2xl text-accent">₹{(totalPrice / 100).toFixed(2)}</p>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 flex justify-between items-center">
            <Link href="/search" className="text-accent hover:underline">
              ← Back to Search
            </Link>
            <button
              onClick={() => setStep('passengers')}
              disabled={selectedSeats.length === 0}
              className="bg-accent hover:bg-accent/90 text-white font-semibold py-3 px-8 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue to Passenger Details →
            </button>
          </div>
        </div>
      )}

      {step === 'passengers' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Passenger Details</h2>
          
          <div className="space-y-4">
            {passengers.map((passenger, index) => (
              <div key={index} className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6">
                <h3 className="font-semibold mb-4">
                  Passenger {index + 1} - Seat: {selectedSeatObjects[index]?.seat_number} ({selectedSeatObjects[index]?.seat_class})
                </h3>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Name</label>
                    <input
                      type="text"
                      value={passenger.name}
                      onChange={(e) => updatePassenger(index, 'name', e.target.value)}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Age</label>
                    <input
                      type="number"
                      value={passenger.age}
                      onChange={(e) => updatePassenger(index, 'age', e.target.value)}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
                      required
                      min="1"
                      max="120"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Gender</label>
                    <select
                      value={passenger.gender}
                      onChange={(e) => updatePassenger(index, 'gender', e.target.value)}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
                    >
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex justify-between items-center">
            <button
              onClick={() => setStep('seats')}
              className="text-accent hover:underline"
            >
              ← Back to Seat Selection
            </button>
            <button
              onClick={() => setStep('confirm')}
              className="bg-accent hover:bg-accent/90 text-white font-semibold py-3 px-8 rounded-lg"
            >
              Continue to Confirmation →
            </button>
          </div>
        </div>
      )}

      {step === 'confirm' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Confirm Booking</h2>
          
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          <div className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-semibold mb-4">Journey Details</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">From</p>
                <p className="font-semibold">{from}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">To</p>
                <p className="font-semibold">{to}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Date</p>
                <p className="font-semibold">{date}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Passengers</p>
                <p className="font-semibold">{passengers.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-semibold mb-4">Selected Seats</h3>
            <div className="space-y-3">
              {selectedSeatObjects.map((seat, index) => (
                <div key={seat.id} className="flex justify-between items-center">
                  <div>
                    <p className="font-semibold">{passengers[index]?.name}</p>
                    <p className="text-sm text-gray-500">
                      Seat {seat.seat_number} - {seat.seat_class}
                    </p>
                  </div>
                  <p className="font-semibold">₹{(seat.price_cents / 100).toFixed(2)}</p>
                </div>
              ))}
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700 mt-4 pt-4">
              <div className="flex justify-between items-center text-lg font-bold">
                <span>Total</span>
                <span>₹{(totalPrice / 100).toFixed(2)}</span>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <button
              onClick={() => setStep('passengers')}
              className="text-accent hover:underline"
              disabled={booking}
            >
              ← Back to Passenger Details
            </button>
            <button
              onClick={handleBook}
              disabled={booking}
              className="bg-accent hover:bg-accent/90 text-white font-semibold py-3 px-8 rounded-lg disabled:opacity-50"
            >
              {booking ? 'Booking...' : 'Confirm & Pay'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
