'use client';

import React, { useState } from 'react';
import { Search, ArrowRight, Bot, Sliders, User, Info } from 'lucide-react';
import { api, BorrowerLookupResponse } from '@/lib/api';
import { useToast } from '@/components/Toast';

// Component imports
import ConnectionStatus from '@/components/operations/ConnectionStatus';
import BorrowerCard from '@/components/operations/BorrowerCard';
import QuickActions from '@/components/operations/QuickActions';
import ActionDrawer from '@/components/operations/ActionDrawer';
import Timeline, { Activity } from '@/components/operations/Timeline';
import KnowledgePanel from '@/components/operations/KnowledgePanel';
import VoiceAssistant from '@/components/operations/VoiceAssistant';

const QUICK_BORROWERS = [
  { id: 'LN001', name: 'Rajesh Kumar' },
  { id: 'LN002', name: 'Priya Sharma' },
  { id: 'LN003', name: 'Amit Patel' },
  { id: 'LN004', name: 'Maria Santos' },
  { id: 'LN005', name: 'Budi Santoso' },
];

export default function OperationsConsole() {
  const { toast } = useToast();

  // Active Borrower Context
  const [borrowerSearchQuery, setBorrowerSearchQuery] = useState('');
  const [searchingBorrower, setSearchingBorrower] = useState(false);
  const [activeBorrower, setActiveBorrower] = useState<BorrowerLookupResponse | null>(null);

  // App API connection state
  const [isApiOnline, setIsApiOnline] = useState(true);

  // Action Drawer State
  const [activeDrawer, setActiveDrawer] = useState<'eligibility' | 'payment' | 'callback' | 'escalation' | null>(null);

  // Session activity logger timeline
  const [activities, setActivities] = useState<Activity[]>([]);

  const handleAddActivity = (act: Activity) => {
    setActivities((prev) => [act, ...prev]);
  };

  const handleBorrowerLookup = async (loanId?: string, name?: string) => {
    const searchVal = loanId || name || borrowerSearchQuery.trim();
    if (!searchVal) {
      toast('Please enter a Loan ID or Borrower Name', 'info');
      return;
    }

    setSearchingBorrower(true);
    try {
      const isLoanId = searchVal.toUpperCase().startsWith('LN') || /^\d+$/.test(searchVal);
      const res = await api.lookupBorrower({
        loan_id: isLoanId ? searchVal.toUpperCase() : null,
        borrower_name: !isLoanId ? searchVal : null,
      });

      if (res.found) {
        setActiveBorrower(res);
        toast(`Loaded profile context: ${res.borrower_name}`, 'success');
        
        handleAddActivity({
          id: Math.random().toString(36).substring(2, 9),
          type: 'borrower_loaded',
          title: 'Borrower File Loaded',
          desc: `Loaded context details for: ${res.borrower_name} (${res.loan_id})`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        });
      } else {
        toast(res.message || 'Borrower not found in database', 'error');
      }
    } catch (err: any) {
      console.error(err);
      toast(err.message || 'Borrower lookup query failed', 'error');
    } finally {
      setSearchingBorrower(false);
    }
  };

  const handleQuickSelect = async (loanId: string) => {
    setBorrowerSearchQuery(loanId);
    await handleBorrowerLookup(loanId);
  };

  const handleClearBorrower = () => {
    if (activeBorrower) {
      toast('Active borrower file context unloaded', 'info');
      setActiveBorrower(null);
      setBorrowerSearchQuery('');
      setActiveDrawer(null);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in text-[var(--foreground)]">
      {/* Header and Connection Status Alert */}
      <div className="space-y-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-white/[0.03] pb-5">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-neutral-900 via-neutral-800 to-neutral-600 dark:from-white dark:via-neutral-200 dark:to-neutral-500 bg-clip-text text-transparent flex items-center gap-2">
              <Sliders className="h-7 w-7 text-indigo-500" />
              AI Operations Console
            </h1>
            <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-1.5 leading-relaxed">
              Verify compliance obections, execute relief workouts, search the Pinecone knowledge index, and connect voice calls.
            </p>
          </div>
        </div>

        {/* Global Connection Beacon Banner */}
        <ConnectionStatus onStatusChange={setIsApiOnline} />
      </div>

      {/* Main Workspace Layout */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        
        {/* LEFT COLUMN: Borrower Profile & Operations Cards (lg:col-span-8) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Borrower search card */}
          <div className="rounded-2xl border border-white/[0.03] bg-neutral-900/10 backdrop-blur-xl p-5 shadow-2xl relative">
            <h2 className="text-sm font-extrabold tracking-tight text-neutral-200 mb-3 flex items-center gap-2">
              <Search className="h-4 w-4 text-indigo-500" />
              Identify Borrower Context
            </h2>

            {/* Quick-select pills */}
            <div className="mb-4">
              <label className="block text-[8px] uppercase tracking-wider font-extrabold text-neutral-500 mb-2">
                Pre-configured Test Profiles
              </label>
              <div className="flex flex-wrap gap-1.5">
                {QUICK_BORROWERS.map((b) => (
                  <button
                    key={b.id}
                    onClick={() => handleQuickSelect(b.id)}
                    className={`px-2.5 py-1 text-[10px] rounded-lg border font-semibold transition-all cursor-pointer ${
                      activeBorrower?.loan_id === b.id
                        ? 'bg-indigo-600/10 border-indigo-550/30 text-indigo-400 font-extrabold'
                        : 'bg-neutral-900 border-white/[0.02] text-neutral-450 hover:text-neutral-250 hover:bg-neutral-800/40'
                    }`}
                  >
                    {b.id} ({b.name.split(' ')[0]})
                  </button>
                ))}
              </div>
            </div>

            {/* Search Input Box */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleBorrowerLookup();
              }}
              className="space-y-3"
            >
              <div className="relative">
                <input
                  type="text"
                  value={borrowerSearchQuery}
                  onChange={(e) => setBorrowerSearchQuery(e.target.value)}
                  placeholder="Query Loan ID (e.g. LN001) or customer name..."
                  className="w-full pl-3.5 pr-12 py-3 bg-neutral-950 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-indigo-500 placeholder-neutral-600 premium-input font-medium shadow-inner"
                />
                <button
                  type="submit"
                  disabled={searchingBorrower}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg transition-all cursor-pointer"
                >
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </form>
          </div>

          {/* Premium profile card context */}
          {activeBorrower ? (
            <div className="space-y-6">
              {/* Borrower detailed card */}
              <BorrowerCard borrower={activeBorrower} onClear={handleClearBorrower} />

              {/* Action Buttons row */}
              <QuickActions hasBorrower={true} onSelectAction={setActiveDrawer} />
            </div>
          ) : (
            /* Empty state profile warning placeholder */
            <div className="rounded-2xl border border-dashed border-white/[0.02] p-10 text-center text-neutral-500 text-xs flex flex-col items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-neutral-950 border border-white/[0.02] text-neutral-600">
                <User className="h-5 w-5" />
              </div>
              <p className="font-semibold text-neutral-400">Borrower file is not selected</p>
              <span className="max-w-xs text-[10px] text-neutral-500 leading-relaxed">
                Use the search query box or select any quick test profile above to trigger relief workflows or dialect callers.
              </span>
            </div>
          )}

          {/* ChatGPT-style RAG Objections Lookup Panel */}
          <KnowledgePanel onLogActivity={handleAddActivity} />
        </div>

        {/* RIGHT COLUMN: Voice Assistant & Timeline telemetry (lg:col-span-4) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Outbound Voice Assistant */}
          <VoiceAssistant borrower={activeBorrower} onLogActivity={handleAddActivity} />

          {/* Activity Logs timeline */}
          <Timeline activities={activities} />
        </div>

      </div>

      {/* Slide-out Action Forms Drawer */}
      <ActionDrawer
        isOpen={activeDrawer !== null}
        type={activeDrawer}
        borrower={activeBorrower}
        onClose={() => setActiveDrawer(null)}
        onActivityLogged={handleAddActivity}
      />
    </div>
  );
}
