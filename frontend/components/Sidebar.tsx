'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  BookOpen, 
  Search, 
  FileCheck, 
  Mic, 
  BarChart3, 
  Activity,
  Layers,
  Sparkles,
  Sliders
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export default function Sidebar({ isOpen, setIsOpen }: SidebarProps) {
  const pathname = usePathname();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Ops Console', href: '/operations', icon: Sliders },
    { name: 'Knowledge Base', href: '/knowledge', icon: BookOpen },
    { name: 'Semantic Search', href: '/search', icon: Search },
    { name: 'Retrieval Test', href: '/retrieval', icon: FileCheck },
    { name: 'Voice Agent', href: '/voice', icon: Mic },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ];

  return (
    <>
      {/* Mobile sidebar backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/80 backdrop-blur-md lg:hidden transition-opacity duration-300"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/[0.03] bg-neutral-950/80 backdrop-blur-xl transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header/Logo */}
        <div className="flex h-16 items-center px-6 border-b border-white/[0.03] gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-indigo-600 shadow-[0_0_15px_rgba(99,102,241,0.35)]">
            <Layers className="h-5 w-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-sm tracking-wider bg-gradient-to-r from-white via-neutral-100 to-neutral-400 bg-clip-text text-transparent">
              LOAN OPS
            </span>
            <span className="text-[9px] uppercase font-bold text-indigo-400 tracking-widest -mt-1 flex items-center gap-1">
              Intelligence <Sparkles className="h-2 w-2" />
            </span>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 space-y-1 px-3 py-6 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={`group flex items-center gap-3 rounded-xl px-4 py-3 text-xs font-semibold transition-all duration-300 ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600/15 to-purple-600/5 text-indigo-450 border border-indigo-500/20 shadow-[0_0_20px_rgba(99,102,241,0.08)]'
                    : 'text-neutral-400 hover:bg-white/[0.02] hover:text-neutral-200 border border-transparent'
                }`}
              >
                <Icon className={`h-4.5 w-4.5 shrink-0 transition-transform duration-200 group-hover:scale-105 ${
                  isActive ? 'text-indigo-400' : 'text-neutral-500 group-hover:text-neutral-400'
                }`} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Footer/System Health */}
        <div className="border-t border-white/[0.03] p-4 bg-black/10">
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-white/[0.03] bg-neutral-900/30 backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-450 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <div className="flex-1 text-[10px]">
              <p className="font-bold text-neutral-350">System Stream</p>
              <p className="text-neutral-500">Operational & ready</p>
            </div>
            <Activity className="h-4 w-4 text-neutral-600" />
          </div>
        </div>
      </aside>
    </>
  );
}
