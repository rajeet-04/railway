'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface Station {
  code: string;
  name: string;
  state: string;
  zone: string;
}

export default function Home() {
  const router = useRouter();
  const [fromStation, setFromStation] = useState('');
  const [toStation, setToStation] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [fromSuggestions, setFromSuggestions] = useState<Station[]>([]);
  const [toSuggestions, setToSuggestions] = useState<Station[]>([]);
  const [showFromDropdown, setShowFromDropdown] = useState(false);
  const [showToDropdown, setShowToDropdown] = useState(false);
  const [fromValid, setFromValid] = useState(false);
  const [toValid, setToValid] = useState(false);
  const [loadingFrom, setLoadingFrom] = useState(false);
  const [loadingTo, setLoadingTo] = useState(false);
  const fromRef = useRef<HTMLDivElement>(null);
  const toRef = useRef<HTMLDivElement>(null);
  const fromTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const toTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (fromRef.current && !fromRef.current.contains(event.target as Node)) {
        setShowFromDropdown(false);
      }
      if (toRef.current && !toRef.current.contains(event.target as Node)) {
        setShowToDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchStations = async (query: string): Promise<Station[]> => {
    // Allow searching for single-character queries as requested
    if (query.length < 1) return [];
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/stations/?q=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        return data;
      }
    } catch (err) {
      console.error('Failed to fetch stations:', err);
    }
    return [];
  };

  const handleFromChange = async (value: string) => {
    setFromStation(value.toUpperCase());
    setFromValid(false);
    
    // Clear previous timeout
    if (fromTimeoutRef.current) {
      clearTimeout(fromTimeoutRef.current);
    }

    if (value.length < 1) {
      setFromSuggestions([]);
      setShowFromDropdown(false);
      return;
    }

    // Debounce API calls
    fromTimeoutRef.current = setTimeout(async () => {
      setLoadingFrom(true);
      const results = await fetchStations(value);
      setFromSuggestions(results);
      setShowFromDropdown(results.length > 0);
      setLoadingFrom(false);
    }, 300);
  };

  const handleToChange = async (value: string) => {
    setToStation(value.toUpperCase());
    setToValid(false);
    
    // Clear previous timeout
    if (toTimeoutRef.current) {
      clearTimeout(toTimeoutRef.current);
    }

    if (value.length < 1) {
      setToSuggestions([]);
      setShowToDropdown(false);
      return;
    }

    // Debounce API calls
    toTimeoutRef.current = setTimeout(async () => {
      setLoadingTo(true);
      const results = await fetchStations(value);
      setToSuggestions(results);
      setShowToDropdown(results.length > 0);
      setLoadingTo(false);
    }, 300);
  };

  const selectFromStation = (station: Station) => {
    setFromStation(station.code);
    setFromValid(true);
    setShowFromDropdown(false);
    setFromSuggestions([]);
  };

  const selectToStation = (station: Station) => {
    setToStation(station.code);
    setToValid(true);
    setShowToDropdown(false);
    setToSuggestions([]);
  };

  const validateStations = async () => {
    // Validate from station
    if (!fromValid) {
      const fromResults = await fetchStations(fromStation);
      const fromExists = fromResults.some(s => s.code === fromStation);
      setFromValid(fromExists);
      if (!fromExists) return false;
    }

    // Validate to station
    if (!toValid) {
      const toResults = await fetchStations(toStation);
      const toExists = toResults.some(s => s.code === toStation);
      setToValid(toExists);
      if (!toExists) return false;
    }

    return true;
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!fromStation || !toStation || !date) {
      return;
    }

    if (fromStation === toStation) {
      alert('From and To stations cannot be the same');
      return;
    }

    const isValid = await validateStations();
    if (!isValid) {
      alert('Please select valid stations from the suggestions');
      return;
    }

    router.push(`/search?from=${fromStation}&to=${toStation}&date=${date}`);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-accent to-accent2 bg-clip-text text-transparent">
          Book Your Train Journey
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Search and book train tickets across India
        </p>
      </div>

      <div className="bg-surface shadow-lg rounded-xl p-8 border border-gray-200 dark:border-gray-800">
        <form onSubmit={handleSearch} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div ref={fromRef} className="relative">
              <label className="block text-sm font-medium mb-2">
                From Station
              </label>
              <input
                type="text"
                value={fromStation}
                onChange={(e) => handleFromChange(e.target.value)}
                placeholder="e.g., NDLS or New Delhi"
                className={`w-full px-4 py-3 rounded-lg border ${
                  fromStation && !fromValid 
                    ? 'border-red-500 dark:border-red-500' 
                    : 'border-gray-300 dark:border-gray-700'
                } bg-white dark:bg-gray-900 focus:ring-2 focus:ring-accent focus:border-transparent`}
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                {loadingFrom ? '🔍 Searching...' : fromStation && !fromValid ? '❌ Invalid station code' : 'Enter station code or name'}
              </p>
              
              {showFromDropdown && fromSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {fromSuggestions.map((station) => (
                    <button
                      key={station.code}
                      type="button"
                      onClick={() => selectFromStation(station)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-700 last:border-b-0"
                    >
                      <div className="font-semibold">{station.code} - {station.name}</div>
                      <div className="text-xs text-gray-500">{station.state} • {station.zone}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div ref={toRef} className="relative">
              <label className="block text-sm font-medium mb-2">
                To Station
              </label>
              <input
                type="text"
                value={toStation}
                onChange={(e) => handleToChange(e.target.value)}
                placeholder="e.g., BCT or Mumbai Central"
                className={`w-full px-4 py-3 rounded-lg border ${
                  toStation && !toValid 
                    ? 'border-red-500 dark:border-red-500' 
                    : 'border-gray-300 dark:border-gray-700'
                } bg-white dark:bg-gray-900 focus:ring-2 focus:ring-accent focus:border-transparent`}
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                {loadingTo ? '🔍 Searching...' : toStation && !toValid ? '❌ Invalid station code' : 'Enter station code or name'}
              </p>
              
              {showToDropdown && toSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {toSuggestions.map((station) => (
                    <button
                      key={station.code}
                      type="button"
                      onClick={() => selectToStation(station)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-700 last:border-b-0"
                    >
                      <div className="font-semibold">{station.code} - {station.name}</div>
                      <div className="text-xs text-gray-500">{station.state} • {station.zone}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="journey-date" className="block text-sm font-medium mb-2">
              Journey Date
            </label>
            <input
              id="journey-date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-accent focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            disabled={(!!fromStation && !fromValid) || (!!toStation && !toValid)}
            className="w-full bg-accent hover:bg-accent/90 text-white font-semibold py-4 px-6 rounded-lg transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            Search Trains
          </button>
        </form>
      </div>

      <div className="mt-12 grid md:grid-cols-3 gap-6">
        <div className="text-center p-6 bg-surface rounded-lg border border-gray-200 dark:border-gray-800">
          <div className="text-3xl mb-2">🚄</div>
          <h3 className="font-semibold mb-2">Fast Booking</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Quick and easy train ticket booking
          </p>
        </div>
        
        <div className="text-center p-6 bg-surface rounded-lg border border-gray-200 dark:border-gray-800">
          <div className="text-3xl mb-2">💺</div>
          <h3 className="font-semibold mb-2">Seat Selection</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Choose your preferred seats
          </p>
        </div>
        
        <div className="text-center p-6 bg-surface rounded-lg border border-gray-200 dark:border-gray-800">
          <div className="text-3xl mb-2">📱</div>
          <h3 className="font-semibold mb-2">Digital Tickets</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Get instant confirmation
          </p>
        </div>
      </div>
    </div>
  );
}
