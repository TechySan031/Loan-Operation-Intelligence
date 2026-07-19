import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

interface StatusCardProps {
  title: string;
  status: 'ok' | 'degraded' | 'error' | 'loading';
  details?: string;
}

export default function StatusCard({ title, status, details }: StatusCardProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'ok':
        return {
          color: 'text-emerald-600 dark:text-emerald-400',
          border: 'border-emerald-500/10 hover:border-emerald-500/20',
          icon: CheckCircle2,
          label: 'Operational',
        };
      case 'degraded':
        return {
          color: 'text-amber-600 dark:text-amber-400',
          border: 'border-amber-500/10 hover:border-amber-500/20',
          icon: AlertTriangle,
          label: 'Degraded',
        };
      case 'loading':
        return {
          color: 'text-indigo-600 dark:text-indigo-400',
          border: 'border-indigo-500/10',
          icon: RefreshCw,
          label: 'Checking...',
          spin: true,
        };
      case 'error':
      default:
        return {
          color: 'text-rose-600 dark:text-rose-455',
          border: 'border-rose-500/10 hover:border-rose-500/20',
          icon: XCircle,
          label: 'Connection Error',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className={`rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-md p-5 transition-all duration-300 hover:-translate-y-0.5 shadow-lg ${config.border} glass-panel`}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-wider font-bold text-neutral-500 dark:text-neutral-450">{title}</span>
        <Icon className={`h-4.5 w-4.5 ${config.color} ${config.spin ? 'animate-spin' : ''}`} />
      </div>
      <div className="mt-3">
        <h3 className={`text-base font-extrabold tracking-tight ${config.color}`}>{config.label}</h3>
        {details && <p className="mt-1 text-[11px] text-neutral-500 dark:text-neutral-400 truncate" title={details}>{details}</p>}
      </div>
    </div>
  );
}
