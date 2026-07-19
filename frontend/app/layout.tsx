'use client';

import React, { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Geist, Geist_Mono } from 'next/font/google';
import Sidebar from '@/components/Sidebar';
import Navbar from '@/components/Navbar';
import { ToastProvider } from '@/components/Toast';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const pathname = usePathname();
  const isLandingPage = pathname === '/';

  React.useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.className = savedTheme === 'dark' ? 'dark scroll-smooth' : 'scroll-smooth';
    } else {
      document.documentElement.className = 'dark scroll-smooth';
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(nextTheme);
    localStorage.setItem('theme', nextTheme);
    document.documentElement.className = nextTheme === 'dark' ? 'dark scroll-smooth' : 'scroll-smooth';
  };

  return (
    <html lang="en" className="dark scroll-smooth">
      <head>
        <title>Loan Operation Intelligence — AI SaaS Dashboard</title>
        <meta name="description" content="AI platform for intelligent loan operations" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen text-[var(--foreground)] bg-[var(--background)] transition-colors duration-300`}
      >
        <ToastProvider>
          {isLandingPage ? (
            children
          ) : (
            <div className="flex min-h-screen overflow-hidden">
              {/* Sidebar */}
              <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
   
              {/* Main content wrapper */}
              <div className="flex flex-col flex-1 min-w-0 overflow-y-auto">
                {/* Top Navbar */}
                <Navbar 
                  sidebarOpen={sidebarOpen} 
                  setSidebarOpen={setSidebarOpen} 
                  theme={theme} 
                  toggleTheme={toggleTheme} 
                />
   
                {/* Main content area */}
                <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
                  {children}
                </main>
              </div>
            </div>
          )}
        </ToastProvider>
      </body>
    </html>
  );
}
