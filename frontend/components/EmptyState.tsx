import React from 'react';
import { HelpCircle, LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionButton?: React.ReactNode;
}

export default function EmptyState({
  title,
  description,
  icon: Icon = HelpCircle,
  actionButton,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8 md:p-12 rounded-2xl border border-dashed border-neutral-900 bg-neutral-900/10 min-h-[300px]">
      <div className="rounded-2xl bg-neutral-900/60 p-4 border border-neutral-800 text-neutral-500 mb-4">
        <Icon className="h-8 w-8" />
      </div>
      <h3 className="text-lg font-bold text-neutral-200">{title}</h3>
      <p className="mt-2 text-sm text-neutral-400 max-w-sm leading-relaxed">{description}</p>
      {actionButton && <div className="mt-6">{actionButton}</div>}
    </div>
  );
}
