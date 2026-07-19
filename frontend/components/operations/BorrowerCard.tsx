'use client';

import React from 'react';
import { User, Calendar, MapPin, Globe, CreditCard, Clock, ShieldAlert, X } from 'lucide-react';
import { BorrowerLookupResponse } from '@/lib/api';

interface BorrowerCardProps {
  borrower: BorrowerLookupResponse;
  onClear: () => void;
}

export default function BorrowerCard({ borrower, onClear }: BorrowerCardProps) {
  // Derive status and risk mappings based on mock borrower profile data
  const getRiskDetails = (loanId: string, daysLeft: number = 5) => {
    if (loanId === 'LN003' || daysLeft <= 2) {
      return { label: 'High Risk', color: 'bg-red-500/10 border-red-500/20 text-red-400' };
    }
    if (loanId === 'LN001' || loanId === 'LN005' || daysLeft <= 5) {
      return { label: 'Medium Risk', color: 'bg-amber-500/10 border-amber-500/20 text-amber-400' };
    }
    return { label: 'Low Risk', color: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' };
  };

  const getLoanStatus = (loanId: string) => {
    if (loanId === 'LN003') return { label: 'Risk of Default', color: 'bg-red-500/10 text-red-400 border-red-500/15' };
    if (loanId === 'LN002') return { label: 'Excellent History', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/15' };
    return { label: 'Active Account', color: 'bg-indigo-500/10 text-indigo-455 border-indigo-500/15' };
  };

  const nameInitials = borrower.borrower_name
    ? borrower.borrower_name.split(' ').map(n => n[0]).join('').toUpperCase()
    : 'B';

  const daysLeft = borrower.days_until_due ?? 5;
  const risk = getRiskDetails(borrower.loan_id ?? '', daysLeft);
  const loanStatus = getLoanStatus(borrower.loan_id ?? '');

  return (
    <div className="relative rounded-2xl border border-white/[0.03] bg-neutral-900/30 backdrop-blur-xl p-5 shadow-2xl overflow-hidden animate-fade-in">
      {/* Decorative colored glow bar at top */}
      <div className="absolute top-0 left-0 right-0 h-[1.5px] bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500" />
      
      {/* Card Header Profile */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3.5">
          {/* Avatar with gradient background */}
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600/35 to-purple-600/10 text-indigo-300 font-extrabold text-sm border border-indigo-550/20 shadow-inner">
            {nameInitials}
          </div>
          <div>
            <h3 className="font-extrabold text-sm text-neutral-100 tracking-tight leading-tight">
              {borrower.borrower_name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="font-mono text-[9px] text-neutral-500 uppercase tracking-widest font-semibold bg-neutral-950 px-1.5 py-0.5 rounded border border-white/[0.03]">
                {borrower.loan_id}
              </span>
              <span className="text-[10px] text-neutral-500 capitalize font-medium">
                {borrower.loan_type} loan
              </span>
            </div>
          </div>
        </div>
        <button
          onClick={onClear}
          className="p-1 rounded-lg bg-white/[0.02] hover:bg-white/[0.06] border border-white/[0.03] text-neutral-450 hover:text-neutral-200 transition-all cursor-pointer"
          title="Unload Borrower Context"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Grid details */}
      <div className="grid grid-cols-2 gap-4 mt-6 border-b border-white/[0.02] pb-5">
        <div>
          <span className="block text-[8px] uppercase tracking-wider font-extrabold text-neutral-500">EMI Balance Due</span>
          <span className="block font-mono font-black text-base text-neutral-200 mt-1">
            {borrower.market === 'india' ? '₹' : borrower.market === 'philippines' ? '₱' : 'Rp '}
            {borrower.amount_due?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
        <div>
          <span className="block text-[8px] uppercase tracking-wider font-extrabold text-neutral-500 text-right">Payment Target</span>
          <span className="block text-right text-xs font-semibold text-neutral-300 mt-1 font-mono flex items-center justify-end gap-1.5">
            <Clock className="h-3 w-3 text-neutral-550" />
            {borrower.due_date}
            <span className={`text-[9px] px-1.5 py-0.5 rounded font-extrabold ${daysLeft <= 3 ? 'bg-red-500/10 text-red-400' : 'bg-neutral-950 text-neutral-400'}`}>
              {daysLeft}d
            </span>
          </span>
        </div>
      </div>

      {/* Badges / Taxonomy Info */}
      <div className="space-y-4 pt-5 text-[11px] leading-relaxed">
        <div className="flex flex-wrap gap-2.5">
          {/* Status Badges */}
          <span className={`px-2 py-0.5 rounded-md border text-[9px] font-extrabold uppercase tracking-wider ${loanStatus.color}`}>
            {loanStatus.label}
          </span>
          <span className={`px-2 py-0.5 rounded-md border text-[9px] font-extrabold uppercase tracking-wider ${risk.color}`}>
            {risk.label}
          </span>
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-neutral-950 border border-white/[0.03] text-[9px] font-bold text-neutral-400 uppercase">
            <MapPin className="h-2.5 w-2.5 text-neutral-550" />
            {borrower.market}
          </span>
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-neutral-950 border border-white/[0.03] text-[9px] font-bold text-neutral-400 uppercase">
            <Globe className="h-2.5 w-2.5 text-neutral-550" />
            {borrower.language}
          </span>
        </div>

        {/* Payment History */}
        <div className="bg-neutral-950/45 p-3 rounded-xl border border-white/[0.02]">
          <span className="block text-[8px] uppercase tracking-wider font-extrabold text-neutral-500 mb-1 flex items-center gap-1">
            <CreditCard className="h-3 w-3 text-neutral-600" />
            Payment History Ledger
          </span>
          <p className="text-[10px] text-neutral-400 font-semibold leading-relaxed">
            {borrower.payment_history}
          </p>
        </div>

        {/* Hardship Program Eligibility list */}
        <div>
          <span className="block text-[8px] uppercase tracking-wider font-extrabold text-neutral-550 mb-2 flex items-center gap-1">
            <ShieldAlert className="h-3 w-3 text-neutral-600" />
            Eligible Relief Offerings
          </span>
          <div className="flex flex-wrap gap-1.5">
            {borrower.eligible_programs?.map((prog) => (
              <span
                key={prog}
                className="px-2 py-0.5 rounded-lg bg-emerald-500/10 border border-emerald-500/15 text-emerald-400 text-[10px] font-bold capitalize shadow-sm"
              >
                {prog.replace('_', ' ')}
              </span>
            )) || <span className="text-neutral-500 text-[10px]">None authorized</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
