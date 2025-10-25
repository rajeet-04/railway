'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface Train {
  id: number;
  number: string;
  name: string;
  type: string;
  train_run_id: number;
  run_date: string;
  available_seats: number;
  total_seats: number;
  status: string;
  journey?: {
    from_station_code: string;
    from_station_name: string;
    to_station_code: string;
    to_station_name: string;
    departure_time: string;
    arrival_time: string;
    departure_day_offset: number;
    arrival_day_offset: number;
    duration: string;
    distance_km: number;
  };
  pricing?: {
    [key: string]: {
      base_fare: number;
      reservation_charge: number;
      total_fare: number;
      total_fare_cents: number;
    };
  };
}

export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [trains, setTrains] = useState<Train[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const from = searchParams.get('from');
  const to = searchParams.get('to');
  const date = searchParams.get('date');

  useEffect(() => {
    if (from && to && date) {
      searchTrains();
    }
  }, [from, to, date]);

  const searchTrains = async () => {
    setLoading(true);
    setError('');

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // First get basic train search results
      const response = await fetch(
        `${apiUrl}/api/trains/search?from=${from}&to=${to}&date=${date}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch trains');
      }

      const basicResults = await response.json();
      
      // Fetch journey details for each train
      const trainsWithDetails = await Promise.all(
        basicResults.map(async (train: Train) => {
          try {
            const journeyResponse = await fetch(
              `${apiUrl}/api/trains/${train.number}/journey?from=${from}&to=${to}&date=${date}`
            );
            
            if (journeyResponse.ok) {
              const journeyData = await journeyResponse.json();
              return {
                ...train,
                journey: journeyData.journey,
                pricing: journeyData.pricing
              };
            }
            return train;
          } catch (err) {
            console.error(`Failed to fetch journey details for train ${train.number}`, err);
            return train;
          }
        })
      );

      setTrains(trainsWithDetails);
    } catch (err) {
      setError('Failed to load trains. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatDayOffset = (offset: number) => {
    if (offset === 0) return '';
    if (offset === 1) return ' (+1 day)';
    return ` (+${offset} days)`;
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-surface h-40 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <Link href="/" className="text-accent hover:underline">
            Back to Search
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Available Trains</h1>
        <p className="text-gray-600 dark:text-gray-400">
          {from} → {to} on {date}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          {trains.length} train(s) found
        </p>
      </div>

      {trains.length === 0 ? (
        <div className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            No trains found for this route and date.
          </p>
          <Link
            href="/"
            className="inline-block bg-accent hover:bg-accent/90 text-white font-semibold py-2 px-6 rounded-lg"
          >
            Try Another Search
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {trains.map((train) => {
            const journey = train.journey;
            
            return (
              <div
                key={train.train_run_id}
                className="bg-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h2 className="text-xl font-semibold">{train.name}</h2>
                      <span className="text-sm text-gray-500">#{train.number}</span>
                      <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400 text-xs font-semibold rounded">
                        {train.type}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 mt-4">
                      <div>
                        <p className="text-sm text-gray-500">Departure</p>
                        <p className="font-semibold text-lg">
                          {journey?.departure_time || 'N/A'}
                          {journey && formatDayOffset(journey.departure_day_offset)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {journey?.from_station_name || from}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-500">Duration</p>
                        <p className="font-semibold">{journey?.duration || 'N/A'}</p>
                        {journey?.distance_km && (
                          <p className="text-xs text-gray-500">{journey.distance_km} km</p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">Arrival</p>
                        <p className="font-semibold text-lg">
                          {journey?.arrival_time || 'N/A'}
                          {journey && formatDayOffset(journey.arrival_day_offset)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {journey?.to_station_name || to}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="md:text-right md:w-48">
                    <div className="mb-3">
                      <p className="text-sm text-gray-500">Available Seats</p>
                      <p className={`font-bold text-lg ${train.available_seats > 20 ? 'text-green-600 dark:text-green-400' : train.available_seats > 0 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'}`}>
                        {train.available_seats} / {train.total_seats}
                      </p>
                    </div>
                    
                    {train.available_seats > 0 ? (
                      <Link
                        href={`/book/${train.number}?from=${from}&to=${to}&date=${date}`}
                        className="inline-block w-full bg-accent hover:bg-accent/90 text-white font-semibold py-3 px-6 rounded-lg transition-all text-center"
                      >
                        Book Now
                      </Link>
                    ) : (
                      <button
                        disabled
                        className="w-full bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 font-semibold py-3 px-6 rounded-lg cursor-not-allowed"
                      >
                        Sold Out
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
