import React, { useState, useRef, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { Menu, Bell, Sun, Moon, ChevronRight, Check, Trash2, X, Info, Database } from 'lucide-react';

interface NavbarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export default function Navbar({ sidebarOpen, setSidebarOpen, theme, toggleTheme }: NavbarProps) {
  const pathname = usePathname();
  const [showNotifications, setShowNotifications] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const [notifications, setNotifications] = useState([
    {
      id: 'n1',
      title: 'Database Connected',
      description: 'PostgreSQL cache, Redis message bus, and Pinecone vector indexes are fully operational.',
      time: 'Just now',
      unread: true,
      category: 'system'
    },
    {
      id: 'n2',
      title: 'Knowledge Base Seeding',
      description: 'Seeded 8 outbound compliance business rules and ingested 15 reference policies.',
      time: '10 mins ago',
      unread: true,
      category: 'knowledge'
    },
    {
      id: 'n3',
      title: 'Voice Agent Ready',
      description: 'Taglish and Bahasa Indonesia bot configurations compiled successfully.',
      time: '1 hour ago',
      unread: false,
      category: 'voice'
    },
    {
      id: 'n4',
      title: 'Model Hot-Reloaded',
      description: 'OpenAI embeddings switched to SentenceTransformer (BGE-small-en) locally.',
      time: '2 hours ago',
      unread: false,
      category: 'ai'
    }
  ]);

  const unreadCount = notifications.filter(n => n.unread).length;

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const toggleRead = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, unread: !n.unread } : n));
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // Close panel on clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getBreadcrumbs = () => {
    if (pathname === '/') return ['Dashboard'];
    const segments = pathname.split('/').filter(Boolean);
    return segments.map(segment => {
      return segment.charAt(0).toUpperCase() + segment.slice(1).replace(/[-_]/g, ' ');
    });
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-[var(--navbar-border)] bg-[var(--navbar-bg)] px-6 backdrop-blur-md transition-all duration-300">
      {/* Left side */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="rounded-lg p-1.5 text-neutral-450 dark:text-neutral-400 hover:bg-neutral-200/50 dark:hover:bg-white/5 hover:text-neutral-800 dark:hover:text-neutral-200 lg:hidden transition-colors"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Breadcrumbs */}
        <nav className="flex items-center space-x-1.5 text-xs font-semibold">
          <span className="text-neutral-450 dark:text-neutral-500 hover:text-neutral-600 dark:hover:text-neutral-400 transition-colors cursor-default">Platform</span>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              <ChevronRight className="h-3.5 w-3.5 text-neutral-300 dark:text-neutral-700 shrink-0" />
              <span className={idx === breadcrumbs.length - 1 ? 'text-indigo-600 dark:text-indigo-400 font-bold bg-indigo-500/10 px-2 py-0.5 rounded-lg border border-indigo-500/10' : 'text-neutral-650 dark:text-neutral-400'}>
                {crumb}
              </span>
            </React.Fragment>
          ))}
        </nav>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Theme Toggle */}
        <div className="flex h-9 items-center gap-1 rounded-xl bg-[var(--pill-bg)] p-1 border border-[var(--card-border)]">
          <button 
            onClick={() => { if (theme !== 'dark') toggleTheme(); }}
            className={`rounded-lg p-1.5 transition-all ${theme === 'dark' ? 'text-indigo-400 bg-[var(--background)] shadow-sm border border-[var(--card-border)]' : 'text-neutral-550 hover:text-neutral-700'}`}
            title="Switch to Dark Mode"
          >
            <Moon className="h-3.5 w-3.5" />
          </button>
          <button 
            onClick={() => { if (theme !== 'light') toggleTheme(); }}
            className={`rounded-lg p-1.5 transition-all ${theme === 'light' ? 'text-indigo-600 bg-[var(--background)] shadow-sm border border-[var(--card-border)]' : 'text-neutral-500 hover:text-neutral-350'}`}
            title="Switch to Light Mode"
          >
            <Sun className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Notification Icon */}
        <div className="relative" ref={panelRef}>
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative rounded-xl border border-[var(--card-border)] bg-[var(--pill-bg)] p-2 text-[var(--text-muted)] hover:bg-[var(--card-bg)] hover:text-[var(--foreground)] transition-all"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-indigo-500 ring-2 ring-white dark:ring-neutral-950 animate-pulse"></span>
            )}
          </button>

          {/* Floating Dropdown Panel */}
          {showNotifications && (
            <div className="absolute right-0 mt-3.5 w-80 md:w-96 rounded-2xl border border-neutral-200/80 dark:border-white/[0.05] bg-white dark:bg-neutral-950 p-4 shadow-xl dark:shadow-[0_20px_50px_rgba(0,0,0,0.5)] animate-fade-in backdrop-blur-xl">
              <div className="flex items-center justify-between border-b border-neutral-100 dark:border-white/[0.03] pb-3 mb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-neutral-800 dark:text-neutral-200">System Updates</h3>
                  {unreadCount > 0 && (
                    <span className="rounded-full bg-indigo-50 dark:bg-indigo-950/50 px-2 py-0.5 text-[10px] font-bold text-indigo-600 dark:text-indigo-400">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button 
                    onClick={markAllAsRead}
                    className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-72 overflow-y-auto space-y-2.5 pr-1">
                {notifications.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-center text-neutral-400 dark:text-neutral-500">
                    <Info className="h-8 w-8 mb-2 stroke-[1.5]" />
                    <p className="text-xs">No updates or notifications</p>
                  </div>
                ) : (
                  notifications.map(n => (
                    <div 
                      key={n.id}
                      onClick={() => toggleRead(n.id)}
                      className={`group relative flex gap-3 rounded-xl p-2.5 transition-all cursor-pointer border ${n.unread ? 'bg-indigo-50/20 dark:bg-indigo-500/[0.02] border-indigo-100/50 dark:border-indigo-500/10' : 'bg-transparent border-transparent hover:bg-neutral-50 dark:hover:bg-white/[0.01]'}`}
                    >
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-neutral-100 dark:bg-neutral-900 text-neutral-500 dark:text-neutral-400">
                        {n.category === 'system' ? <Database className="h-3.5 w-3.5 text-blue-500" /> : <Info className="h-3.5 w-3.5 text-indigo-500" />}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className={`text-xs font-bold truncate ${n.unread ? 'text-neutral-900 dark:text-neutral-100' : 'text-neutral-500 dark:text-neutral-400'}`}>
                            {n.title}
                          </p>
                          <span className="text-[9px] text-neutral-400 dark:text-neutral-500 shrink-0">{n.time}</span>
                        </div>
                        <p className={`text-[11px] leading-relaxed mt-0.5 line-clamp-2 ${n.unread ? 'text-neutral-600 dark:text-neutral-350' : 'text-neutral-400 dark:text-neutral-500'}`}>
                          {n.description}
                        </p>
                      </div>

                      {/* Hover actions */}
                      <div className="absolute right-2 top-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteNotification(n.id);
                          }}
                          className="rounded-md p-1 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-white/[0.05] text-neutral-450 hover:text-red-500 hover:border-red-500/20 shadow-sm transition-all"
                          title="Dismiss"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User profile */}
        <div className="flex items-center gap-3 border-l border-[var(--navbar-border)] pl-4">
          <div className="hidden text-right md:block">
            <p className="text-xs font-bold text-[var(--foreground)] opacity-95">Saniya</p>
            <p className="text-[9px] font-semibold text-[var(--text-muted)] tracking-wider">LEAD AI ENGINEER</p>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-extrabold text-sm shadow-[0_0_15px_rgba(99,102,241,0.25)] border border-indigo-400/20">
            S
          </div>
        </div>
      </div>
    </header>
  );
}
