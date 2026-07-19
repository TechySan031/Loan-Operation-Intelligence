import React, { ElementType } from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon | ElementType;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  loading?: boolean;
}

export default function MetricCard({
  title,
  value,
  icon: Icon,
  change,
  changeType = 'positive',
  loading = false,
}: MetricCardProps) {
  return (
    <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 hover:bg-[var(--card-bg)]/80 transition-all duration-300 hover:-translate-y-0.5 shadow-xl backdrop-blur-md glow-card-indigo glass-panel">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-450">{title}</span>
        <div className="rounded-xl bg-indigo-500/5 p-2.5 border border-indigo-500/10 text-indigo-500 dark:text-indigo-400">
          <Icon className="h-4.5 w-4.5" />
        </div>
      </div>
      <div className="mt-4">
        {loading ? (
          <div className="h-9 w-24 animate-pulse rounded-lg bg-neutral-200 dark:bg-neutral-900" />
        ) : (
          <h2 className="text-3xl font-extrabold text-neutral-900 dark:text-neutral-100 tracking-tight">{value}</h2>
        )}

        {!loading && change && (
          <div className="mt-2.5 flex items-center gap-1.5 text-[10px] font-bold">
            <span
              className={`rounded px-1.5 py-0.5 ${
                changeType === 'positive'
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/10'
                  : changeType === 'negative'
                  ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/10'
                  : 'bg-neutral-100 dark:bg-neutral-900 text-neutral-500 border border-[var(--card-border)]'
              }`}
            >
              {change}
            </span>
            <span className="text-neutral-500 dark:text-neutral-450 uppercase tracking-wide">vs last cycle</span>
          </div>
        )}
      </div>
    </div>
  );
}
