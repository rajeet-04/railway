'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function Header() {
  const { theme, setTheme } = useTheme();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    setMounted(true);
    // Check if user is logged in
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    setUser(null);
    router.push('/');
  };

  return (
    <header className="border-b border-gray-200 dark:border-gray-800 bg-surface">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold text-accent hover:text-accent/80">
            🚂 Railway Booking
          </Link>
          
          <nav className="flex items-center gap-6">
            <Link href="/" className="hover:text-accent">
              Search
            </Link>
            {user && (
              <Link href="/bookings" className="hover:text-accent">
                My Bookings
              </Link>
            )}
            
            {mounted && (
              <>
                {user ? (
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Hi, {user.full_name || user.email}
                    </span>
                    <button
                      onClick={handleLogout}
                      className="text-red-600 dark:text-red-400 hover:underline"
                    >
                      Logout
                    </button>
                  </div>
                ) : (
                  <Link href="/auth/login" className="hover:text-accent">
                    Login
                  </Link>
                )}
                
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                  aria-label="Toggle theme"
                >
                  {theme === 'dark' ? '🌞' : '🌙'}
                </button>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
