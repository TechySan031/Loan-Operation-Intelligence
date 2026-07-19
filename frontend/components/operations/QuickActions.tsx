'use client';

import React from 'react';
import { UserCheck, CreditCard, Calendar, ShieldAlert } from 'lucide-react';

interface QuickActionsProps {
  hasBorrower: boolean;
  onSelectAction: (type: 'eligibility' | 'payment' | 'callback' | 'escalation') => void;
}

export default function QuickActions({ hasBorrower, onSelectAction }: QuickActionsProps) {
  const actions = [
    {
      id: 'eligibility' as const,
      label: 'Check Relief Eligibility',
      desc: 'Verify eligibility for hardship/EMI deferrals',
      icon: UserCheck,
      color: 'hover:border-indigo-500/30 group-hover:text-indigo-400',
      iconBg: 'bg-indigo-600/10 text-indigo-400 border-indigo-500/20',
    },
    {
      id: 'payment' as const,
      label: 'Record Payment Commitment',
      desc: 'Log borrower commitment date and method',
      icon: CreditCard,
      color: 'hover:border-emerald-500/30 group-hover:text-emerald-400',
      iconBg: 'bg-emerald-600/10 text-emerald-400 border-emerald-500/20',
    },
    {
      id: 'callback' as const,
      label: 'Schedule Outbound Callback',
      desc: 'Queue phone callback for target date-time',
      icon: Calendar,
      color: 'hover:border-amber-500/30 group-hover:text-amber-400',
      iconBg: 'bg-amber-600/10 text-amber-400 border-amber-500/20',
    },
    {
      id: 'escalation' as const,
      label: 'Human Agent Escalation',
      desc: 'Route file to human collections supervisor',
      icon: ShieldAlert,
      color: 'hover:border-rose-500/30 group-hover:text-rose-455',
      iconBg: 'bg-rose-600/10 text-rose-400 border-rose-500/20',
    },
  ];

  return (
    <div className="space-y-3.5">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-bold uppercase tracking-wider text-neutral-500">
          Agent Operations Actions
        </h2>
        {!hasBorrower && (
          <span className="text-[10px] text-neutral-500 italic font-medium">
            * Select a borrower to enable actions
          </span>
        )}
      </div>

      <div className="grid gap-3.5 sm:grid-cols-2 md:grid-cols-4">
        {actions.map((act) => {
          const Icon = act.icon;
          return (
            <button
              key={act.id}
              onClick={() => onSelectAction(act.id)}
              disabled={!hasBorrower}
              className={`group relative text-left p-4 rounded-xl border border-white/[0.02] bg-neutral-900/10 backdrop-blur-md transition-all duration-300 flex flex-col justify-between hover:bg-white/[0.01] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
                hasBorrower ? act.color : ''
              }`}
            >
              <div className="flex flex-col gap-3">
                <div className={`flex h-8 w-8 items-center justify-center rounded-lg border shadow-inner transition-transform duration-300 group-hover:scale-105 ${act.iconBg}`}>
                  <Icon className="h-4.5 w-4.5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-xs text-neutral-250 transition-colors duration-200 group-hover:text-neutral-100">
                    {act.label}
                  </h3>
                  <p className="text-[10px] text-neutral-500 font-semibold leading-relaxed mt-1">
                    {act.desc}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
