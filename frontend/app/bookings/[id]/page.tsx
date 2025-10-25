'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface BookingDetail {
  booking_id: string;
  train_number: string;
  train_name: string;
  from_station_code: string;
  to_station_code: string;
  from_station_name: string;
  to_station_name: string;
  journey_date: string;
  booking_time: string;
  total_cents: number;
  num_passengers: number;
  status: string;
  payment_status: string;
  passengers: Array<{
    passenger_name: string;
    passenger_age: number;
    passenger_gender: string;
    seat_number: string;
    seat_class: string;
    price_cents: number;
  }>;
}

export default function BookingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bookingId = params.id as string;

  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    fetchBookingDetails();
  }, [bookingId]);

  const fetchBookingDetails = async () => {
    setLoading(true);
    setError('');

    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/auth/login');
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/bookings/${bookingId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch booking details');
      }

      const data = await response.json();
      setBooking(data);
    } catch (err) {
      setError('Failed to load booking details. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this booking?')) {
      return;
    }

    setCancelling(true);
    setError('');

    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/auth/login');
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/bookings/${bookingId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to cancel booking');
      }

      // Refresh booking details
      await fetchBookingDetails();
      alert('Booking cancelled successfully');
    } catch (err) {
      setError('Failed to cancel booking. Please try again.');
      console.error(err);
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="animate-pulse bg-surface h-96 rounded-lg"></div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error || 'Booking not found'}</p>
          <Link href="/bookings" className="text-accent hover:underline">
            Back to My Bookings
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <Link href="/bookings" className="text-accent hover:underline mb-4 inline-block">
          ← Back to My Bookings
        </Link>
        <h1 className="text-3xl font-bold">Booking Details</h1>
      </div>

      <div className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-2xl font-semibold mb-2">{booking.train_name}</h2>
            <p className="text-gray-600 dark:text-gray-400">Train #{booking.train_number}</p>
            <p className="text-sm text-gray-500 mt-2">
              Booked on: {new Date(booking.booking_time).toLocaleString()}
            </p>
          </div>
          <div className="text-right">
            <span
              className={`inline-block px-4 py-2 rounded-full text-sm font-semibold ${
                booking.status === 'CONFIRMED'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                  : booking.status === 'CANCELLED'
                  ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                  : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
              }`}
            >
              {booking.status}
            </span>
          </div>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-600 dark:text-blue-400 font-semibold mb-1">PNR Number</p>
          <p className="text-2xl font-bold text-blue-800 dark:text-blue-300">{booking.booking_id}</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-6">
          <div>
            <p className="text-sm text-gray-500 mb-1">From</p>
            <p className="font-semibold text-lg">{booking.from_station_name}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{booking.from_station_code}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">To</p>
            <p className="font-semibold text-lg">{booking.to_station_name}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{booking.to_station_code}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Journey Date</p>
            <p className="font-semibold text-lg">{booking.journey_date}</p>
          </div>
        </div>
      </div>

      <div className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 mb-6">
        <h3 className="text-xl font-semibold mb-4">Passenger Details</h3>
        <div className="space-y-4">
          {booking.passengers?.map((passenger, index) => (
            <div
              key={index}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
            >
              <div className="grid md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Name</p>
                  <p className="font-semibold">{passenger.passenger_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Age</p>
                  <p className="font-semibold">{passenger.passenger_age}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Gender</p>
                  <p className="font-semibold">
                    {passenger.passenger_gender === 'M' ? 'Male' : passenger.passenger_gender === 'F' ? 'Female' : 'Other'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Seat</p>
                  <p className="font-semibold">{passenger.seat_number} ({passenger.seat_class})</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 mb-6">
        <h3 className="text-xl font-semibold mb-4">Payment Details</h3>
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm text-gray-500">Payment Status</p>
            <p className={`font-semibold ${booking.payment_status === 'PAID' ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
              {booking.payment_status}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Total Amount</p>
            <p className="text-2xl font-bold">₹{(booking.total_cents / 100).toFixed(2)}</p>
          </div>
        </div>
      </div>

      {booking.status === 'CONFIRMED' && (
        <div className="flex justify-end">
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-8 rounded-lg disabled:opacity-50"
          >
            {cancelling ? 'Cancelling...' : 'Cancel Booking'}
          </button>
        </div>
      )}
    </div>
  );
}
