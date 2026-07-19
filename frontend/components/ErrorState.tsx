import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({
  title = 'Connection Alert',
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8 rounded-2xl border border-white/[0.03] bg-neutral-900/10 backdrop-blur-xl min-h-[250px] shadow-xl">
      <div className="rounded-2xl bg-amber-500/10 p-3.5 border border-amber-500/20 text-amber-400 mb-4 animate-pulse">
        <AlertCircle className="h-6 w-6" />
      </div>
      <h3 className="text-base font-extrabold text-neutral-200 tracking-tight">{title}</h3>
      <p className="mt-1.5 text-xs text-neutral-500 max-w-md font-semibold leading-relaxed">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 flex items-center gap-2 rounded-xl bg-indigo-600/10 hover:bg-indigo-650/20 px-4 py-2 text-xs font-bold text-indigo-400 border border-indigo-500/25 transition-all duration-200 cursor-pointer shadow-md"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Reconnect Service
        </button>
      )}
    </div>
  );
}
