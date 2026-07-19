'use client';

import React from 'react';
import { User, UserCheck, CreditCard, Calendar, ShieldAlert, PhoneCall, Bot, HelpCircle } from 'lucide-react';

export interface Activity {
  id: string;
  type: 'borrower_loaded' | 'eligibility_checked' | 'payment_recorded' | 'callback_scheduled' | 'escalated' | 'voice_started' | 'knowledge_retrieved';
  title: string;
  desc: string;
  timestamp: string;
}

interface TimelineProps {
  activities: Activity[];
}

export default function Timeline({ activities }: TimelineProps) {
  const getIcon = (type: Activity['type']) => {
    switch (type) {
      case 'borrower_loaded':
        return { icon: User, color: 'text-indigo-400 border-indigo-500/20 bg-indigo-500/10' };
      case 'eligibility_checked':
        return { icon: UserCheck, color: 'text-purple-400 border-purple-500/20 bg-purple-500/10' };
      case 'payment_recorded':
        return { icon: CreditCard, color: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10' };
      case 'callback_scheduled':
        return { icon: Calendar, color: 'text-amber-400 border-amber-500/20 bg-amber-500/10' };
      case 'escalated':
        return { icon: ShieldAlert, color: 'text-rose-455 border-rose-500/20 bg-rose-500/10' };
      case 'voice_started':
        return { icon: PhoneCall, color: 'text-teal-400 border-teal-500/20 bg-teal-500/10' };
      case 'knowledge_retrieved':
        return { icon: Bot, color: 'text-cyan-400 border-cyan-500/20 bg-cyan-500/10' };
      default:
        return { icon: HelpCircle, color: 'text-neutral-400 border-neutral-500/20 bg-neutral-550/10' };
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xs font-bold uppercase tracking-wider text-neutral-500">
        Session Activity Log
      </h2>

      <div className="rounded-2xl border border-white/[0.03] bg-neutral-900/10 backdrop-blur-xl p-5 shadow-2xl relative">
        {activities.length === 0 ? (
          <div className="py-8 text-center text-neutral-500 text-xs font-medium flex flex-col items-center gap-2">
            <Bot className="h-6 w-6 text-neutral-600 animate-pulse" />
            <span>No activities recorded in the current ops session.</span>
          </div>
        ) : (
          <div className="relative pl-6 space-y-6">
            {/* Vertical timeline connector line */}
            <div className="absolute left-2.5 top-2 bottom-2 w-[1px] bg-white/[0.03]" />

            {activities.map((act) => {
              const { icon: Icon, color: iconStyle } = getIcon(act.type);

              return (
                <div key={act.id} className="relative flex gap-4 animate-fade-in text-xs">
                  {/* Timeline point icon wrapper */}
                  <div className={`absolute -left-6 flex h-5 w-5 items-center justify-center rounded-full border shadow-sm ${iconStyle}`}>
                    <Icon className="h-3 w-3 shrink-0" />
                  </div>

                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-neutral-200 tracking-tight leading-tight">
                        {act.title}
                      </span>
                      <span className="text-[9px] font-bold text-neutral-500 font-mono">
                        {act.timestamp}
                      </span>
                    </div>
                    <p className="text-[10px] text-neutral-500 font-semibold leading-normal">
                      {act.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
